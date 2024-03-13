#!/usr/bin/python3.11
# startup command: ./startup_2.py

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

NUM_DOMAIN = 2

# WARNING: Temporally hardcoded openflow port (ofp) to 6633+i

# create startup sequence
# ryu startup
for i in range(NUM_DOMAIN):
  subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                    f'{RYU_MANAGER} --observe-links --ofp-tcp-listen-port={6633+i} --wsapi-port={RYU_PORT+i} \
                      ryu.app.ofctl_rest {RYUAPP_DIR}/manualswitch.py \
                      {RYUAPP_CONTROLLERREST} {RYUAPP_FLOWMANAGER};\
                    read -p "press any key to close"'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)


# Load from file
subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 
                  f'sudo PYTHONPATH={os.getenv("PYTHONPATH")} \
                    {VENV11} ./scenario/mn_network/networkfromfile_multicontroler.py \
                    ./scenario/mn_network/graphml_ds/Epoch.graphml {NUM_DOMAIN} -apip \
                    {RESTHOOKMN_PORT} -ofp 6633;\
                    read -p "press any key to close"'], 
                    stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

# input('press enter to continue')

time.sleep(5)
# dynamicsdn startup
subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                  f'{EXPORT_PYTHONPATH};\
                    {VENV11} ./routingapp/main.py {RESTDYNAMICSDN_PORT} {RYU_PORT} \
                      -md true;\
                    read -p "press any key to close"'], 
                    stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

# time.sleep(1)
# # sdn_db startup
# subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
#                   f'{EXPORT_PYTHONPATH};\
#                     {VENV11} ./sdndb/crawler.py {RYU_PORT};\
#                     read -p "press any key to close"'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

time.sleep(1)
# scenario startup
# subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
#                   f'{VENV11} {SCENARIO_DIR}/scenario_test.py {RESTHOOKMN_PORT} {RESTDYNAMICSDN_PORT};\
#                   read -p "press any key to close"'], 
#                   stderr=subprocess.STDOUT, stdout=subprocess.PIPE)





