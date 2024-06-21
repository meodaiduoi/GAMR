#! /home/onos/Desktop/ryu/venv11/bin/python3.11

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Link
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.util import irange
from mininet.link import TCLink, Intf

# import uvicorn
# from mn_restapi.mn_restapi_hook import RestHookMN 

import time
import sys
import os

# import argparse
# argParser = argparse.ArgumentParser()
# argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")
# argParser.add_argument("openflow_port", type=int, default=6633, help="open flow connect port")
# # argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port")
# args = argParser.parse_args()

# RESTHOOKMN_PORT = args.rest_port
# OFP_PORT = args.openflow_port

class MyTopo(Topo):
    def build(self):
        h1 =  self.addHost('h1')
        h2 =  self.addHost('h2')

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        
        # ep_list = [(h1, s1), (h2, s2), (h3, s3), (h4, s4)]
        # link_route = [(s1, s2), (s2, s3), (s3, s4), (s4, s1)]

        # for d1, d2 in ep_list:
        #     self.addLink(d1, d2)
        # for d1, d2 in link_route:
        #     self.addLink(d1, d2)
        self.addLink(h1,s1)
        self.addLink(s1,s2, bw=10, delay='10ms', loss=0.05)
        self.addLink(h2,s2)

def changeBandwith( node ):
  for intf in node.intfList(): # loop on interfaces of node
    #info( ' %s:'%intf )
    if intf.link: # get link that connects to interface(if any)
        newBW = 5
        
        # intfs = [ intf.link.intf1, intf.link.intf2 ] #intfs[0] is source of link and intfs[1] is dst of link
        # intfs[0].config(bw=newBW) 
        # intfs[1].config(bw=newBW)
    else:
        info( ' \n' )

def manageLinks():
    nodes = net.switches + net.hosts
    for node in nodes:
        changeBandwith(node)

if __name__ == '__main__':
    
    setLogLevel( 'info' )
    try:
        # c0 = RemoteController('c0', ip='0.0.0.0', port=OFP_PORT)
        net = Mininet( topo=MyTopo(), 
                      autoSetMacs=True,
                      link=TCLink,
                      ipBase='10.0.0.0/24')
        net.start()

        print(type(net.get('s1').intfList()))
        print(type(net.get('s1').intfList()[1].link))
        print(net.topo.linkInfo('s1', 's2'))

        print('//')

        print(net.get('s1').connectionsTo(net.get('s2')))
        
        # belong to mininet.link.TCLink
        print(type(net.get('s1').connectionsTo(net.get('s2'))[0][0]))
        intfs = net.get('s1').connectionsTo(net.get('s2'))[0]
        intfs[0].config(bw=20, loss=50) 
        intfs[1].config(bw=20, loss=50)
        print()
        # intfs = [ intf.link.intf1, intf.link.intf2 ] #intfs[0] is source of link and intfs[1] is dst of link
        # intfs[0].config(bw=newBW) 
        # intfs[1].config(bw=newBW)
        print(type(net.topo.linkInfo('s1', 's2')))

        print('update dict')
        net.topo.linkInfo('s1', 's2').update({'bw': 20, 'loss':50})
        print(net.topo.linkInfo('s1', 's2'))
        
        # app = RestHookMN(net=net)sud
        # uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
        CLI(net)
        net.stop()
    
    except Exception as e:
        print(e)
        time.sleep(10)
        net.stop()