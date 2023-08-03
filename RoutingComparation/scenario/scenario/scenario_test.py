import requests as rq
from helper.utils import *
import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("resthookmn_port", type=int, help="resthookmn remote rest api port")
argParser.add_argument("restdynamicsdn_port", type=int, default=6633, help="restdynamicsdn port")
# argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port")
args = argParser.parse_args()

RESTHOOKMN_PORT = args.resthookmn_port
RESTDYNAMICSDN_PORT =  args.restdynamicsdn_port

if __name__ == '__main__':
    # devicename = rq.get(f'http://0.0.0.0:{RESTHOOKMN_PORT}/device_name').json()
    # hostname = devicename['hostname']
    # switchname = devicename['switchname']
    
    # Link probing seq
    rq.get(f'http://0.0.0.0:{RESTHOOKMN_PORT}/link_probing')
    

    
    
    

