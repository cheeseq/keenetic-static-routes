# keenetic-static-routes
In SOVIET ЯUSSIA your "FirstPythonPetProject" is not a TODO app or Telegram bot... it's a tool for setting up VPN split-tunneling to get access to needed IP addresses via VPN.

If you are Keenetic user and your model supports REST API, this tools might help you.
Currently supports adding static routes as IP addresses or with domains (resolve IP via DNS A record).
Also supports transfering static routes from one interface to another.
WARNING: code contains about 1337 bugs, but i'm too lazy to find and fix them. At least this script works for me :D
Usage:

 1. `pip install -r requirements.txt`
 2. Configure your keenetic.conf.example file and rename it to keenetic.conf. default_interface option is an ID of interface on which static routes will be added.
 3. `python rkn.py COMMAND`