#! /home/onos/Desktop/ryu/venv11/bin/python3.11


from mininet.topo import Topo
from mininet.net import Mininet

from mininet.cli import CLI
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink

from mininet.log import setLogLevel

# import uvicorn
# from mn_restapi.mn_restapi_hook import RestHookMN
from mn_restapi.util import *

import random
random.seed(69)

import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")
argParser.add_argument("openflow_port", type=int, default=6653, help="open flow connect port")
args = argParser.parse_args()

RESTHOOKMN_PORT = args.rest_port
OFP_PORT = args.openflow_port

class MyTopo(Topo):
    def build(self):
        h1 =  self.addHost('h1')
        h2 =  self.addHost('h2')
        h3 =  self.addHost('h3')
        h4 =  self.addHost('h4')
        
        # s1 = self.addSwitch('s1', protocols='OpenFlow13')
        # s2 = self.addSwitch('s2', protocols='OpenFlow13')
        # s3 = self.addSwitch('s3', protocols='OpenFlow13')
        # s4 = self.addSwitch('s4', protocols='OpenFlow13')

        s1 = self.addSwitch('s1', stp=True)
        s2 = self.addSwitch('s2', stp=True)
        s3 = self.addSwitch('s3', stp=True)
        s4 = self.addSwitch('s4', stp=True)

        ep_list = [(h1, s1), (h2, s2), (h3, s3), (h4, s4)]
        link_route = [(s1, s2), (s2, s3), (s3, s4), (s4, s1)]
        # link_route = [(s1, s2), (s2, s3), (s3, s4)]
        
        for d1, d2 in ep_list:
            self.addLink(d1, d2, delay=f'{random.randint(1, 10)}ms', loss=random.randint(0, 1), max_queue_size=1000, use_htb=True)
        for d1, d2 in link_route:
            self.addLink(d1, d2, delay=f'{random.randint(10, 30)}ms', loss=random.randint(0, 10), max_queue_size=1000, use_htb=True)

if __name__ == '__main__':
    setLogLevel( 'info' )
    # add ccontroller and build the network
    c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet(topo=MyTopo(), 
                  controller=c0,
                  switch=OVSSwitch,
                  link=TCLink,
                  autoSetMacs=True,
                  ipBase='10.0.0.0')
    net.start()
    
    # enable_stp(net)
    # wait_for_stp(net)
    
    # app = RestHookMN(net=net)
    # uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
    CLI(net)
    net.stop()