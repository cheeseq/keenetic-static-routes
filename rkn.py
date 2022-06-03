# -*- coding: utf-8 -*-

CONFIG_FILE_NAME = "keenetic.conf"
ADDED_ROUTES_FILE_NAME = "added_static_routes.csv"
REQUESTS_INTERVAL_SEC = 0.3

import csv
import time
import keenetic
import click
import dns.resolver
from urllib.parse import urlparse
from pathlib import Path

@click.group()
@click.pass_context
def cli(ctx):
    ctx.obj = keenetic.Keenetic(CONFIG_FILE_NAME)
    f = Path(ADDED_ROUTES_FILE_NAME)
    f.touch(exist_ok=True)

@cli.command()
@click.option('--routes', help='IP addresses or URLS delimited with |')
@click.pass_obj
def add_route(keenetic, routes):
    """Adding a static routes to configured Keenetic router. Accepts IPv4, IPv6 adrresses or URLs, which hostname is extracted, and lookuped to ip through DNS"""
    if routes:
        _add_routes(keenetic, routes)
    else:
        while True:
            routes = click.prompt("IP addresses or URLS delimited with |")
            _add_routes(keenetic, routes)    
    

def _add_routes(keenetic, routes):
    routes = routes.split("|")
    routes_ips = []
    with open(ADDED_ROUTES_FILE_NAME, "r+", newline="") as csv_file:
        existing_routes = set()
        csv_reader = csv.reader(csv_file, "excel")
        for existing_route in csv_reader:
            existing_routes.add(existing_route[0])
        
        csv_writer = csv.writer(csv_file, "excel")

        for route in routes:
            url = urlparse(route)
            if url.netloc:
                answers = dns.resolver.resolve(url.netloc, 'A')
                for a in answers:
                    routes_ips.append(a.to_text())
            else:
                routes_ips.append(route)
            
        for ip in routes_ips:
            if ip not in existing_routes:
                if keenetic.add_ip_route(ip):
                    existing_routes.add(ip)
                    csv_writer.writerow([ip, keenetic.default_interface])
            time.sleep(REQUESTS_INTERVAL_SEC)

@cli.command()
@click.argument('to')
@click.pass_obj
def replace_interface(keenetic, to):    
    """Transfers your currently added routes to the specified interface"""
    with open(ADDED_ROUTES_FILE_NAME, "r", newline="") as added_routes_file:
        existing_routes = set()
        csv_reader = csv.reader(added_routes_file, "excel")
        for existing_route in csv_reader:
            existing_routes.add(existing_route)

    with open(ADDED_ROUTES_FILE_NAME, "w+", newline="") as added_routes_file:
        csv_writer = csv.writer(added_routes_file, "excel")
        out_routes = []
        err_routes = []

        #write to csv routes with new interface or if deletion is not successful, write with old interface
        for route in existing_routes:
            if keenetic.delete_ip_route(route[0]):
                time.sleep(REQUESTS_INTERVAL_SEC)
                if keenetic.add_ip_route(route[0], to):
                    csv_writer.writerow([route[0], to])
                else:
                    err_routes.append(route[0])
            else:
                out_routes.append(route)
            time.sleep(REQUESTS_INTERVAL_SEC)

        if len(err_routes) > 0:
            print("There are error routes:")  
            for err_route in err_routes:
                print(err_route)

if __name__ == '__main__':
    cli()