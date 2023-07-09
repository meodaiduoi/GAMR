#!/home/onos/Desktop/bknet/venv11/bin/python3.11

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node , Controller, RemoteController, OVSSwitch
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import irange
from mininet.link import TCLink

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from ..mn_restapi.mn_restapi_hook import RestHook 

class MyTopo(Topo):
    def build(self):
        h1 =  self.addHost('h1')
        h2 =  self.addHost('h2')
        h3 =  self.addHost('h3')
        h4 =  self.addHost('h4')
        
        s1 = self.addSwitch('s1' ,protocols='OpenFlow13')
        s2 = self.addSwitch('s2' ,protocols='OpenFlow13')
        s3 = self.addSwitch('s3' ,protocols='OpenFlow13')
        s4 = self.addSwitch('s4' ,protocols='OpenFlow13')

        ep_list = [(h1, s1), (h2, s2), (h3, s3), (h4, s4)]
        link_route = [(s1, s2), (s2, s3), (s3, s4), (s4, s1)]

        for d1, d2 in ep_list:
            self.addLink(d1, d2)
        for d1, d2 in link_route:
            self.addLink(d1, d2)

if __name__ == '__main__':
    
    setLogLevel( 'info' )
    
    c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet( topo=MyTopo(), controller=c0, 
                  autoSetMacs=True,
                  ipBase='10.0.0.0')
    net.start()
    app = RestHook(net=net)
    uvicorn.run(app, host="0.0.0.0", port=8000)

    net.stop()
