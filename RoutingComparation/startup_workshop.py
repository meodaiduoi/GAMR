#!/usr/bin/python3.11
import subprocess, time
import tomllib

try:
    with open("config.toml", "rb") as f:
        toml_dict = tomllib.load(f)
except tomllib.TOMLDecodeError:
    print("Yep, definitely not valid.")

# ENV variable
RYU_MANAGER = toml_dict['venv-path']['ryu-manager-python7']
VENV11 = toml_dict['venv-path']['venv11']
RYUAPP_DIR = toml_dict['app-path']['ryuapp-dir']
RYUAPP_CONTROLLERREST = toml_dict['app-path']['ryuapp-controllerrest']
RYUAPP_FLOWMANAGER = toml_dict['app-path']['ryuapp-flowmanager']

SCENARIO_DIR = toml_dict['app-path']['scenario-dir']
SDNDB = toml_dict['app-path']['sdndb']

RYU_PORT = toml_dict['service-port']['ryu']
RESTHOOKMN_PORT = toml_dict['service-port']['resthookmn']
RESTDYNAMICSDN_PORT = toml_dict['service-port']['dynamicsdn']
OFP_PORT = toml_dict['service-port']['ofp']

import os
EXPORT_PYTHONPATH = f'export PYTHONPATH={os.getenv("PYTHONPATH")}'
print(EXPORT_PYTHONPATH)

# create startup sequence
NUM_DOMAIN = 2
# ryu startup
for i in range(NUM_DOMAIN):
  subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                    f'{RYU_MANAGER} --observe-links --ofp-tcp-listen-port={6633+i} --wsapi-port={RYU_PORT+i} \
                      ryu.app.ofctl_rest {RYUAPP_DIR}/manualswitch.py \
                      {RYUAPP_CONTROLLERREST} {RYUAPP_FLOWMANAGER};\
                    read -p "press any key to close"'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 
                  f'sudo PYTHONPATH={os.getenv("PYTHONPATH")} \
                    {VENV11} ./scenario/mn_network/2c2s.py; \
                    read -p "press any key to close"'], 
                    stderr=subprocess.STDOUT, stdout=subprocess.PIPE)