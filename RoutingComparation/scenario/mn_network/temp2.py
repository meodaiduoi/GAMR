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


# import uvicorn
# from mn_restapi.mn_restapi_hook import RestHookMN 

# import argparse
# argParser = argparse.ArgumentParser()
# argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")
# argParser.add_argument("openflow_port", type=int, default=6633, help="open flow connect port")
# # argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port")
# args = argParser.parse_args()

# RESTHOOKMN_PORT = args.rest_port
# OFP_PORT = args.openflow_port

class MyTopo( Topo ):
    def build(self, *args, **params):
        s1 = self.addSwitch('s1', protocols='OpenFlow13', stp=True)
        s2 = self.addSwitch('s2', protocols='OpenFlow13', stp=True)
        s3 = self.addSwitch('s3', protocols='OpenFlow13', stp=True)

        # Add hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')

        # Add links
        self.addLink(h1, s1, bw=500, delay='2ms', max_queue_size=1000, loss=1, use_htb=True)
        self.addLink(h2, s2, bw=500, delay='3ms', max_queue_size=1000, loss=1, use_htb=True)
        self.addLink(h3, s3, bw=500, delay='5ms', max_queue_size=1000, loss=1, use_htb=True)
        self.addLink(s1, s2, bw=500, delay='20ms', max_queue_size=1000, loss=5, use_htb=True)
        self.addLink(s2, s3, bw=500, delay='15ms', max_queue_size=1000, loss=6, use_htb=True)
        self.addLink(s3, s1, bw=500, delay='22ms', max_queue_size=1000, loss=4, use_htb=True)


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
    s1 = net.get('s1')
    s2 = net.get('s2')
    s3 = net.get('s3')
    s1.cmd('ovs-vsctl set Bridge %s stp_enable=true' % s1.name)
    s2.cmd('ovs-vsctl set Bridge %s stp_enable=true' % s2.name)
    s3.cmd('ovs-vsctl set Bridge %s stp_enable=true' % s3.name)
    CLI(net)
    net.stop()
    
