from mininet.net import Mininet
from mininet.link import TCLink
#!/home/onos/Desktop/ryu/venv11/bin/python3.11

import os
import random

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node, CPULimitedHost, Host

from mininet.cli import CLI
from mininet.link import Intf
from mininet.node import Controller, RemoteController, OVSSwitch, OVSKernelSwitch

from mininet.topolib import TreeTopo
from mininet.link import TCLink

from mininet.log import setLogLevel, info
from mininet.util import pmonitor


# import uvicorn
# from mn_restapi.mn_restapi_hook import RestHookMN 

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
        
        swlink = [(s1, s2), (s2, s3), (s3, s1)]
        for d1, d2 in swlink:
            self.addLink(d1, d2, bw=100, delay='30ms', loss=0, use_htb=True)
    
if __name__ == '__main__':
    setLogLevel( 'info' )
    # add ccontroller and build the network
    # c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet( topo=MyTopo(), 
                #   controller=c0, 
                    autoSetMacs=True,
                    link=TCLink,
                    ipBase='10.0.0.0')
    net.start()
    
    # Using prebuilt fastapi restapi
    # app = RestHookMN(net=net)
    # uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
    CLI(net)
    net.stop()
    