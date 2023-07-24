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


# import uvicorn
# from mn_restapi.mn_restapi_hook import RestHookMN 

import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")
argParser.add_argument("openflow_port", type=int, default=6633, help="open flow connect port")
# argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port")
args = argParser.parse_args()

RESTHOOKMN_PORT = args.rest_port
OFP_PORT = args.openflow_port

class MyTopo( Topo ):
    def build(self, *args, **params):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')        
        s3 = self.addSwitch('s3')

        links = [(h1, s1), (h2, s2), 
                 (h3, s3), (s1, s2), (s2, s3)]
        
        for a, b in links:
            self.addLink(a, b)
            
if __name__ == '__main__':
    setLogLevel( 'info' )
    # add ccontroller and build the network
    c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet( topo=MyTopo(), controller=c0, 
                    autoSetMacs=True,
                    ipBase='10.0.0.0')
    net.start()
    # app = RestHookMN(net=net)
    # uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
    CLI(net)
    net.stop()