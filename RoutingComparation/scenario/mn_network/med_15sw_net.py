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

import random

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
        
        device_num = 16
        swlist = []
        for i in range(1, device_num):
            swlist = self.addSwitch(f's{i}')
        
        hlist = []
        for i in range()
            for i in range(1, device_num):
                hlist = self.addHost(f'h{i}')
 
        for d1, d2 in swlist, hlist:
            self.addLink(d1, d2)

        # 
        for d1 in swlist:
            for d2 in reversed(swlist):
                if random.random() < 0.75:
                    self.addLink(d1, d2)
        
        

if __name__ == '__main__':
    setLogLevel( 'info' )
    # add ccontroller and build the network
    c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet(topo=MyTopo(), 
                  controller=c0,
                  switch=OVSSwitch,
                  autoSetMacs=True,
                  ipBase='10.0.0.0')
    net.start()

    # net.configLinkStatus('s1', 's4', 'down')
    # net.pingAllFull()
    # net.configLinkStatus('s1', 's4', 'up')
    # net.configLinkStatus('s1', 's2', 'down')
    # net.pingAllFull()
    
    # s1: Node = net.get('s1')
    # s4: Node = net.get('s4')
    
    # link1 = s1.linkTo(s4)
    # link1.delete() # Bring down the link from h1 to s1

    # Perform your desired actions with the link down

    # Bring the link back up
    # link1.intf1.link_up()  # Bring up the link from h1 to s1
    
    app = RestHookMN(net=net)
    uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
    CLI(net)
    net.stop()