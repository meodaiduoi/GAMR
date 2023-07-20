#!/usr/bin/python3.11
import subprocess
import tomllib

try:
    with open("config.toml", "rb") as f:
        toml_dict = tomllib.load(f)
except tomllib.TOMLDecodeError:
    print("Yep, definitely not valid.")

# ENV variable
VENV11 = toml_dict['venv-path']['venv11']
VENV7 = toml_dict['venv-path']['venv7']
RYU_MANAGER = toml_dict['venv-path']['ryu-manager']
RYU = toml_dict['app-path']['ryu']

RYU_PORT = toml_dict['service-port']['ryu']
RESTHOOKMN_PORT = toml_dict['service-port']['resthookmn']
RESTDYNAMICSDN_PORT = toml_dict['service-port']['dynamicsdn']
OFP_PORT = toml_dict['service-port']['ofp']

# create startup sequence
# mininet + mnresthook startup
subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 
                  f'{VENV11} ./RoutingComparation/scenario/mn_network/dyamic_linearnet.py {RESTHOOKMN_PORT} {OFP_PORT}'], 
                 stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

# ryu startup
subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                  f'{RYU_MANAGER} --ofp-tcp-listen-port={OFP_PORT} --wsapi-port={RYU_PORT} ryu.app.ofctl_rest ryu.app.simple_switch_13 {RYU}'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

# dynamicsdn startup
subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                  f'{VENV11} ./RoutingComparation/dynamicsdn/rest_dynamicsdn.py {RESTDYNAMICSDN_PORT} {RYU_PORT}'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

# datalogging startup
# subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', command], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)




