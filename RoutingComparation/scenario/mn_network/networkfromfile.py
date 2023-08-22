#! /home/onos/Desktop/ryu/venv11/bin/python3.11

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
random.seed(69)

from mn_restapi.util import * 
from mn_restapi.mn_restapi_hook import *
import uvicorn
    
import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("filepath", type=str, help="graphml file path")
argParser.add_argument("-apip", "--api_port",type=int, default=8000, help="resthookmn startup rest api port")
argParser.add_argument("-ofp", "--openflow_port", type=int, default=6653, help="open flow connect port")
args = argParser.parse_args()

RESTHOOKMN_PORT = args.api_port
OFP_PORT = args.openflow_port
FILEPATH = args.filepath

if __name__ == '__main__':
    setLogLevel( 'info' )
    
    # You can change this function for your own file format
    graph: nx.Graph = nx.read_graphml(FILEPATH)
    
    # add ccontroller and build the network
    c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet(controller=None,
                  switch=OVSSwitch,
                  link=TCLink,
                  ipBase='10.0.0.0/24')
    
    # Construct mininet
    for n in graph.nodes:
        # Overide start index from 0 to 1
        n = int(n) + 1
        
        net.addSwitch(f"s{n}", stp=True)
        # Add single host on designated switches

        net.addHost(f"h{n}", mac=int_to_mac(n))
        # directly add the link between hosts and their gateways
        # There is no point adding spec at endpoint because we cant mesuare it anyway
        net.addLink(f's{n}', f'h{n}',
                    max_queue_size=1000, use_htb=True)
    
    # Connect your switches to each other as defined in networkx graph
    spec_list = {}
    for (n1, n2) in graph.edges:
        
        # Overide start index from 0 to 1
        n1 = int(n1) + 1
        n2 = int(n2) + 1
        
        net.addLink(f's{n1}', f's{n2}',
                    bw=random.randint(50, 100),
                    delay=f'{random.randint(10, 50)}ms',
                    loss=random.randint(0, 4),
                    max_queue_size=1000, use_htb=True
                    )
    
    # ARP must be enable if you want adding flow manually
    net.staticArp()
    net.start()

    # Enable spanning tree protocol (optional)
    enable_stp(net)
    wait_for_stp(net)
    
    # app = RestHookMN(net=net)
    # uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
    CLI(net)
    net.stop()