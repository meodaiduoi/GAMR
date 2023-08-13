from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI


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

from mn_restapi.util import *



"Simple topology example."
class MyTopo( Topo ):
    def build( self ):
        "Create custom topo."
        # Add hosts and switches
        h1 =  self.addHost( 'h1',  ip='10.10.2.1/24' ,mac='00:00:00:00:00:01',defaultRoute='via 10.10.2.254' )
        h2 =  self.addHost( 'h2',  ip='10.10.2.2/24', mac='00:00:00:00:00:02',defaultRoute='via 10.10.2.254' )
        
        sc1 = self.addSwitch( 'sc1', dpid='0000000000000001', stp=True )
        sc2 = self.addSwitch( 'sc2', dpid='0000000000000002', stp=True )
        sc3 = self.addSwitch( 'sc3', dpid='0000000000000003', stp=True )
        sc4 = self.addSwitch( 'sc4', dpid='0000000000000004', stp=True )

        self.addLink( sc1, h1 )
        self.addLink( sc1, sc4 )
        self.addLink( sc4, sc2 )
        self.addLink( sc1, sc3 )
        self.addLink( sc2, sc3 )
        self.addLink( sc2, h2 )

        
if __name__ == '__main__':
    setLogLevel( 'info' )
    # add ccontroller and build the network
    c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet( topo=MyTopo(), 
                  controller=c0, 
                    autoSetMacs=True,
                    switch=OVSSwitch,
                    link=TCLink,
                    ipBase='10.0.0.0')
    net.start()
    # app = RestHookMN(net=net)
    # uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
    
    # enable_stp(net)
    # wait_for_stp(net)
    

    CLI(net)
    net.stop()