#!/usr/bin/python3.11
# startup command: ./startup_2.py

import os, sys, subprocess, time
from os.path import dirname, abspath

import logging
import tomllib

try:
    with open("config.toml", "rb") as f:
        logging.info('Loading config.toml')
        toml_dict = tomllib.load(f)
except tomllib.TOMLDecodeError:
  logging.fatal('config.toml decoding error, exiting...')
  sys.exit(1)

# ENV variable
RYU_MANAGER = toml_dict['venv-path']['ryu-manager-python7']
VENV11 = toml_dict['venv-path']['venv11']
RYUAPP_DIR = toml_dict['app-path']['ryuapp-dir']
RYUAPP_CONTROLLERREST = toml_dict['app-path']['ryuapp-controllerrest']
RYUAPP_FLOWMANAGER = toml_dict['app-path']['ryuapp-flowmanager']

SCENARIO_DIR = toml_dict['app-path']['scenario-dir']
SDNDB = toml_dict['app-path']['sdndb']

# Service Port
RYU_PORT = toml_dict['service-port']['ryu']
OFP_PORT = toml_dict['service-port']['ofp'] 
os.environ['RYU_PORT'] = str(RYU_PORT)
os.environ['OFP_PORT'] = str(OFP_PORT)
os.environ['RESTHOOKMN_PORT'] = RESTHOOKMN_PORT = str(toml_dict['service-port']['resthookmn'])
os.environ['ROUTING_APP_PORT'] = ROUTING_APP_PORT = str(toml_dict['service-port']['routingapp'])

# Multidomain config
MULTI_DOMAIN = toml_dict['app-setting']['scenario-multidomain']
os.environ['MULTI_DOMAIN'] = str(MULTI_DOMAIN)
NUM_DOMAIN = toml_dict['app-setting']['scenario-num-domain']
TOPO_FILE = toml_dict['app-setting']['scenario-topo-file']

# PYTHONPATH debug
if os.environ.get('PYTHONPATH') != None:
  logging.info(f'WDIR: export PYTHONPATH={os.getenv("PYTHONPATH")}')
if os.environ.get('PYTHONPATH') == None:
  logging.warning('export PYTHONPATH is not set script will try to adding PYTHONPATH at running script parent dir')
  EXPORT_PYTHONPATH = dirname(abspath(__file__))
  logging.info(f'Adding  PYTHONPATH at {EXPORT_PYTHONPATH}')

# Startup config debug loging
logging.info('System startup with running config:')
logging.info(f'MULTI_DOMAIN: {os.getenv("MULTI_DOMAIN")}')
logging.info(f'RYU_PORT: {os.getenv("RYU_PORT")}')
logging.info(f'OFP_PORT: {os.getenv("OFP_PORT")}')
logging.info(f'RESTHOOKMN_PORT: {os.getenv("RESTHOOKMN_PORT")}')
logging.info(f'ROUTING_APP_PORT: {os.getenv("ROUTING_APP_PORT")}')
logging.info(f'NUM_DOMAIN: {NUM_DOMAIN}')
logging.info(f'TOPO_FILE: {TOPO_FILE}')

# create startup sequence
# ryu startup
logging.info(f'Running Ryu')
if MULTI_DOMAIN is False:
  subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                    f'{RYU_MANAGER} --observe-links --ofp-tcp-listen-port={OFP_PORT} --wsapi-port={RYU_PORT} \
                      ryu.app.ofctl_rest {RYUAPP_DIR}/manualswitch.py \
                      {RYUAPP_FLOWMANAGER} {RYUAPP_CONTROLLERREST};\
                    read -p "press any key to close"'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

if MULTI_DOMAIN is True:
  for i in range(NUM_DOMAIN):
    subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                      f'{RYU_MANAGER} --observe-links --ofp-tcp-listen-port={OFP_PORT+i} --wsapi-port={RYU_PORT+i} \
                        ryu.app.ofctl_rest {RYUAPP_DIR}/manualswitch.py \
                        {RYUAPP_CONTROLLERREST} {RYUAPP_FLOWMANAGER};\
                      read -p "press any key to close"'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

time.sleep(1)
# Load from file
logging.info('Running mininet')
if MULTI_DOMAIN == False:
  subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 
                    f'sudo PYTHONPATH={EXPORT_PYTHONPATH} \
                      {VENV11} ./scenario/mn_network/networkfromfile.py \
                      ./scenario/mn_network/graphml_ds/{TOPO_FILE} \
                      -apip {RESTHOOKMN_PORT} -ofp {OFP_PORT};\
                      read -p "press any key to close"'], 
                      stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

if MULTI_DOMAIN == True:
  subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', 
                    f'sudo PYTHONPATH={EXPORT_PYTHONPATH} \
                      {VENV11} ./scenario/mn_network/networkfromfile_multicontroler.py \
                      ./scenario/mn_network/graphml_ds/{TOPO_FILE} {NUM_DOMAIN} \
                      -apip {RESTHOOKMN_PORT} -ofp {OFP_PORT};\
                      read -p "press any key to close"'], 
                      stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

time.sleep(5)
# rouitngapp
logging.info('Running routing app')
subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
                  f'PYTHONPATH={EXPORT_PYTHONPATH} \
                    {VENV11} ./routingapp/routing_app.py;\
                    read -p "press any key to close"'], 
                    stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

# time.sleep(1)
# # sdn_db startup
# # subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
# #                   f'PYTHONPATH={EXPORT_PYTHONPATH} \
# #                     {VENV11} ./sdndb/crawler.py {RYU_PORT};\
# #                     read -p "press any key to close"'], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

# time.sleep(1)
# # scenario startup
# # subprocess.Popen(['gnome-terminal', '--', 'bash', '-c',
# #                   f'PYTHONPATH={EXPORT_PYTHONPATH} {VENV11} {SCENARIO_DIR}/scenario_test.py {RESTHOOKMN_PORT} {RESTDYNAMICSDN_PORT};\
# #                   read -p "press any key to close"'], 
# #                   stderr=subprocess.STDOUT, stdout=subprocess.PIPE)





