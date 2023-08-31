#! /home/onos/Desktop/ryu/venv11/bin/python3.11

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node , Controller, RemoteController, OVSSwitch
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import irange
from mininet.link import TCLink

from extras.utils import *
from mn_restapi.util import * 
from mn_restapi.mn_restapi_hook import *
import uvicorn

import time
import sys
import os

import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")
argParser.add_argument("openflow_port", type=int, default=6633, help="open flow connect port")
# argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port")
args = argParser.parse_args()

RESTHOOKMN_PORT = args.rest_port
OFP_PORT = args.openflow_port

class MyTopo(Topo):
    def build(self):
        h1 =  self.addHost('h1')
        h2 =  self.addHost('h2')
        h3 =  self.addHost('h3')
        h4 =  self.addHost('h4')
        
        s1 = self.addSwitch('s1', stp=True)
        s2 = self.addSwitch('s2', stp=True)
        s3 = self.addSwitch('s3', stp=True)
        s4 = self.addSwitch('s4', stp=True)

        ep_list = [(h1, s1), (h2, s2), (h3, s3), (h4, s4)]
        link_route = [(s1, s2), (s2, s3), (s3, s4)]

        for d1, d2 in ep_list:
            self.addLink(d1, d2)
        for d1, d2 in link_route:
            self.addLink(d1, d2, loss=5, bandwidth=20, delay='20ms')

if __name__ == '__main__':
    setLogLevel( 'info' )
    try:
        c0 = RemoteController('c0', ip='0.0.0.0', port=OFP_PORT)
        net = Mininet( topo=MyTopo(), 
                       controller=c0, 
                      switch=OVSSwitch,
                      autoSetMacs=True,
                      link=TCLink,
                      ipBase='10.0.0.0')
        net.staticArp()
        net.start()
        
        net.getNodeByName('h1').cmd('xterm -e ech')
        
        # app = RestHookMN(net=net)
        # uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
        CLI(net)
        net.stop()
    
    except Exception as e:
        print(e)
        time.sleep(10)
        net.stop()