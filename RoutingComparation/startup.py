#!/usr/bin/python3.11
# startup command: ./startup_2.py
import subprocess, time
import tomllib
import os

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


EXPORT_PYTHONPATH = f'export PYTHONPATH={os.getenv("PYTHONPATH")}'
print(EXPORT_PYTHONPATH)
# create startup sequence

startup_seq = [1, 2, 3]

# ryu startup
if 1 in startup_seq:
  subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                    f'{RYU_MANAGER} --observe-links --ofp-tcp-listen-port={OFP_PORT} --wsapi-port={RYU_PORT} ryu.app.ofctl_rest {RYUAPP_DIR}/manualswitch.py \
                      {RYUAPP_DIR}/temp.py {RYUAPP_FLOWMANAGER} {RYUAPP_CONTROLLERREST};\
                      read -p "press any key to close"'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
  # DEbug
  # subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
  #                   f'{RYU_MANAGER} --observe-links --ofp-tcp-listen-port={OFP_PORT} --wsapi-port={RYU_PORT} ryu.app.ofctl_rest {RYUAPP_DIR}/simple_switch_13.py {RYUAPP_FLOWMANAGER} {RYUAPP_CONTROLLERREST};\
  #                   read -p "press any key to close"'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
  time.sleep(1)

if 2 in startup_seq:
  # mininet + mnresthook startup
  # subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
  #                   f'{VENV11} ./scenario/mn_network/med_15sw_net.py {RESTHOOKMN_PORT} {OFP_PORT};\
  #                   read -p "press any key to close"'],
  #                  stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

  # Load from file
  subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                    f'sudo PYTHONPATH={os.getenv("PYTHONPATH")} \
                      {VENV11} ./scenario/mn_network/networkfromfile.py \
                      ./scenario/mn_network/graphml_ds/HostwayInternational.graphml -apip \
                      {RESTHOOKMN_PORT} -ofp {OFP_PORT};\
                      read -p "press any key to close"'],
                      stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
  time.sleep(5)

if 3 in startup_seq:
  # dynamicsdn startup
  subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                    f'{EXPORT_PYTHONPATH};\
                      {VENV11} ./dynamicsdn/routing.py {RESTDYNAMICSDN_PORT} {RYU_PORT};\
                      read -p "press any key to close"'],
                      stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

  time.sleep(1)

if 4 in startup_seq:
# sdn_db startup
  subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                    f'{EXPORT_PYTHONPATH}; \
                      {VENV11} ./sdndb/crawler.py {RYU_PORT}; \
                      read -p "press any key to close"'],
                      stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
  time.sleep(1)

# scenario startup
# subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
#                   f'{VENV11} {SCENARIO_DIR}/scenario_test.py {RESTHOOKMN_PORT} {RESTDYNAMICSDN_PORT};\
#                   read -p "press any key to close"'],
#                   stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
