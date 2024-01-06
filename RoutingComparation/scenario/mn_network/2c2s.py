from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, CPULimitedHost

from mininet.cli import CLI
from mininet.link import Intf
from mininet.node import Controller, RemoteController, OVSSwitch, OVSKernelSwitch

from mininet.topolib import TreeTopo
from mininet.link import TCLink, Link

from mininet.log import setLogLevel, info
from mininet.util import pmonitor

import networkx as nx

import random
# random.seed(69)

from extras.utils import *
from scenario.common.utils import *
from mn_restapi.util import * 
from mn_restapi.mn_restapi_hook import *
import uvicorn

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
            self.addLink(d1, d2)

if __name__ == '__main__':
    setLogLevel( 'info' )
    # add ccontroller and build the network
    c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet(topo=MyTopo(), 
                  autoSetMacs=True,
                  link=TCLink,
                  ipBase='10.0.0.0')
    net.staticArp()
    net.start()
    
    net.addController(f'c1', 
                controller=RemoteController,
                ip='0.0.0.0', port=6633)
    
    net.addController(f'c2', 
                controller=RemoteController,
                ip='0.0.0.0', port=6634)
    
    net.get('s1').start([net.get('c1')])
    net.get('s2').start([net.get('c1')])
    net.get('s3').start([net.get('c2')])
    net.get('s4').start([net.get('c2')])
    
    # Using prebuilt restapi (fastapi) Optional
    # app = RestHookMN(net, )
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    
    # Check switch-controller connection status
    # net.get('s1').cmdPrint('ovs-vsctl show')
    
    CLI(net)
    net.stop()