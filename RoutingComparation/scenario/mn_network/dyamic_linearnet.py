#! /home/onos/Desktop/ryu/venv11/bin/python3.11

import os
import random

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, CPULimitedHost

from mininet.cli import CLI
from mininet.link import Intf
from mininet.node import Controller, RemoteController, OVSSwitch, OVSKernelSwitch

from mininet.topolib import TreeTopo
from mininet.link import TCLink

from mininet.log import setLogLevel, info
from mininet.util import pmonitor

import uvicorn
from mn_restapi.mn_restapi_hook import RestHookMN 

import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")
argParser.add_argument("openflow_port", type=int, default=6633, help="open flow connect port")
# argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port")
args = argParser.parse_args()

RESTHOOKMN_PORT = args.rest_port
OFP_PORT = args.openflow_port

class MyTopo( Topo ):
    # Builds network topology
    def build( self, **_opts ):

        # Adding clients
        number_of_clients = 3
        clients = [ self.addHost( f'h{n}', cpu=0.3 ) for n in range(1, number_of_clients) ]      
        ep_clients = [ self.addSwitch( f'ep_cl{n}' ) for n in range(1, number_of_clients) ]
        for h, s in zip(clients, ep_clients):
            self.addLink(h, s,
                         cls=TCLink,
                         bw=10,
                         delay='2ms',)
        
        # Adding servers
        number_of_servers = 3
        servers = [ self.addHost( f'sv{n}', cpu=0.3 ) for n in range(1, number_of_servers) ]
        ep_servers = [ self.addSwitch( f'ep_sv{n}' ) for n in range(1, number_of_servers) ] 
        for sv, ep_sv in zip(servers, ep_servers):
            self.addLink(sv, ep_sv,
                         cls=TCLink,
                         bw=100,
                         delay='2ms',)
       
        # number of level
        number_of_layer = 2
        # Number of switches in each level
        switch_in_level = 2
        
        layers_of_switches = []
        for i in range(number_of_layer):
            switches = [ self.addSwitch( f'sw{i}_{j}' ) for j in range(switch_in_level) ]
            layers_of_switches.append(switches)
        
        # add ep_clients to the first layer and ep_servers to the last layer
        layers_of_switches.insert(0, ep_clients)
        layers_of_switches.append(ep_servers)
        
        # connect switches between adjacent layers
        for i in range(len(layers_of_switches)-1):
            for sw1 in layers_of_switches[i]:
                for sw2 in layers_of_switches[i+1]:
                    self.addLink(sw1, sw2,
                                 cls=TCLink,
                                 bw=100,
                                 delay='2ms',
                                 loss=2)
            
def run():
    setLogLevel( 'info' )
    # add ccontroller and build the network
    c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet(topo=MyTopo(), 
                  controller=c0, 
                  autoSetMacs=True,
                  link=TCLink,
                  ipBase='10.0.0.0')
    net.start()
    app = RestHookMN(net=net)
    uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
    # CLI(net)
    net.stop()
    
if __name__ == '__main__':
    setLogLevel( 'info' )
    run()