import hashlib
import ipaddress
from msilib.schema import Error
import requests
import configparser
import click

cookies_current = None
session = requests.session()

class Keenetic:

    def __init__(self, config_file_name) -> None:
        config = configparser.ConfigParser()  
        config.read(config_file_name)

        self.ip_addr = config["Router"]["ip_addr"]
        self.login = config["Router"]["login"]
        self.password = config["Router"]["password"]
        self.default_interface = config["Router"]["default_interface"]

    def keen_request(self, query, post = None):
        global session
        url = "http://" + self.ip_addr + "/" + query

        if post:
            return session.post(url, json=post)
        else:
            return session.get(url)

    def keen_auth(self):
        response = self.keen_request("auth")
        if response.status_code == 401:
            md5 = self.login + ":" + response.headers["X-NDM-Realm"] + ":" + self.password
            md5 = hashlib.md5(md5.encode('utf-8'))
            sha = response.headers["X-NDM-Challenge"] + md5.hexdigest()
            sha = hashlib.sha256(sha.encode('utf-8'))
            response = self.keen_request("auth", {"login": self.login, "password": sha.hexdigest()})
            if response.status_code == 200:
                click.echo("Auth completed")
                return True
            else:
                raise RuntimeError(f"Cannot authorise on {self.ip_addr}")
        elif response.status_code == 200:
            return True
        else:
            return False

    def __validate_ip(self, ip):
        try:
            return ipaddress.ip_address(ip)
        except ValueError:
            return False

    def get_routes(self):
        if not self.keen_auth():
            raise RuntimeError("Cannot authorize")

        response = self.keen_request("rci/show/ip/route").json()
        routes = dict()
        for item in response:
            if item["interface"] == self.default_interface:
                dst = self.__strip_netmask(item["destination"])
                routes[dst] = item
        return routes

    def get_routes_by_interface(self):
        if not self.keen_auth():
            raise RuntimeError("Cannot authorize")

        response = self.keen_request("rci/show/ip/route").json()
        routes = dict()
        routes[self.default_interface] = list()
        for item in response:
            if item["interface"] == self.default_interface:
                dst = self.__strip_netmask(item["destination"])
                routes[self.default_interface].append(dst)
        return routes

    def __strip_netmask(self, ip):
        slash = ip.find("/")
        if slash == -1:
            return ip
        else:
            return ip[0:slash]


    def add_ip_route(self, route_ip, interface=False):
        if not interface:
            interface = self.default_interface

        existing_routes = self.get_routes().keys()
        if route_ip in existing_routes:
            click.echo(f"Route already exists {route_ip}")
            return

        ip_type = self.__validate_ip(route_ip)
        if not ip_type:
            return False
        elif ip_type.version == 4:
            method = 'rci/ip/route'
        elif ip_type.version == 6:
            method = 'rci/ip6/route'
        else:
            raise RuntimeError(f"Undefined ip address type {type(ip_type)}, version {ip_type.version}")

        response = self.keen_request(method, {"host": route_ip, "interface": interface, "auto": True})
        if not response.ok:
            click.echo(f"Error adding static ip route {route_ip} on interface {interface}, response {response.text}, status {response.status_code}")
            return False

        response = response.json()
        if response["status"][0]["status"] != "error":
            click.echo(f"Added static ip route {route_ip} on interface {interface}, response: {response}")
            return True
        else:
            message = response["status"][0]["message"]
            click.echo(f"Error adding static ip route {route_ip} on interface {interface}, error message {message}")
            return False

    def delete_ip_route(self, route_ip, interface=False):
        if not interface:
            interface = self.default_interface

        if not self.keen_auth():
            raise RuntimeError("Cannot authorize")

        ip_type = self.__validate_ip(route_ip)
        if not ip_type:
            return False
        elif ip_type.version == 4:
            method = 'rci/ip/route'
        elif ip_type.version == 6:
            method = 'rci/ip6/route'
        else:
            raise RuntimeError(f"Undefined ip address type {type(ip_type)}, version {ip_type.version}")

        response = self.keen_request(method, {"host": route_ip, "interface": interface, "no": True})
        if not response.ok:
            click.echo(f"Error deleting static ip route {route_ip} on interface {interface}, response {response.text}, status {response.status_code}")
            return False

        response = response.json()
        if response["status"][0]["status"] != "error":
            click.echo(f"Deleted static ip route {route_ip} on interface {interface}, response: {response}")
            return True
        else:
            message = response["status"][0]["message"]
            click.echo(f"Error deleting static ip route {route_ip} on interface {interface}, error message {message}")
            return False