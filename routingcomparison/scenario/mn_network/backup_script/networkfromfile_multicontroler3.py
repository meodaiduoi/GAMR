
#!/usr/bin/python3.11

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

from RoutingComparison.routingcomparison.extras.network_info_utils import *
from scenario.common.utils import *
from mn_restapi.mn_hook_util import * 
from mn_restapi.mn_restapi_hook import *
import uvicorn
    
import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("filepath", type=str, help="graphml file path")
argParser.add_argument("num_parts", type=int, help="number of sdn domain")
argParser.add_argument("-apip", "--api_port",type=int, default=8000, help="resthookmn startup rest api port")
argParser.add_argument("-ofp", "--openflow_port", type=int, default=6653, help="open flow connect port")

args = argParser.parse_args()
RESTHOOKMN_PORT = args.api_port
OFP_PORT = args.openflow_port
FILEPATH = args.filepath
NUM_PARTITION = args.num_parts
# import os
# PYTHONPATH = os.getenv('PYTHONPATH')


def myNet(graph: nx.Graph, part_graph):
    
    net = Mininet(
        switch=OVSSwitch,
        link=TCLink,
        ipBase='10.0.0.0/24',
        topo=None, build=False
    )

    net.graph = graph
    net.link_quality = []
    net.debug_sw_host_mapping = {}


    # Construct mininet
    for n in net.graph.nodes:
        '''
            Overide start index from 0 to 1 for 
            mininet convention host and sw starting from 1
        '''
        n = int(n) + 1
        
        # set switch dpid and host mac addr
        sw = net.addSwitch(f"s{n}", dpid=str(n).zfill(16), stp=True)
        # Add single host on designated switches
        net.addHost(f"h{n}", mac=int_to_mac(n))
        
        '''
            Directly add the link between hosts and their gateways
            there is no point adding spec at endpoint because 
            we cant mesuare it anyway
        '''
        net.addLink(f's{n}', f'h{n}',
                    max_queue_size=1000, use_htb=True)

        '''
            This section is for adding dummy hosts for
            debugging purpose do not use these hosts in
            runtime. (Currently using for mesuaring link
            delay and packet loss)
        '''
        # Convention id
        debug_id = n*1000
        debug_host = net.addHost(f"h{debug_id}", mac=int_to_mac(debug_id))
        # Add debug dummy host to switch
        net.addLink(f's{n}', f'h{debug_id}',
                        max_queue_size=1000, use_htb=True)
        # Save mapping for later use
        net.debug_sw_host_mapping[str(sw)] = str(debug_host)         
        
    # Connect your switches to each other as defined in networkx graph
    for (n1, n2) in net.graph.edges:
        
        # Overide start index from 0 to 1
        n1 = int(n1) + 1
        n2 = int(n2) + 1
        
        # link param using norm dist
        loss = normdist_array_genparam([0.1, 0.5, 1, 2, 3, 4, 5, 7, 9, 10])
        delay = normdist_array_genparam(range(5, 100))
        bw = normdist_array_genparam(range(30, 200))
        
        # add link with these following param
        net.addLink(f's{n1}', f's{n2}',
                    bw=bw,
                    delay=f'{delay}ms',
                    loss=loss,
                    max_queue_size=1000, use_htb=True)
        
        # Save link stats for later use
        data = {'src.dpid': n1, 'dst.dpid': n2, 
                'packet_loss': loss, 'delay': delay, 'bandwidth': bw }
        net.link_quality.append(data)
        data = {'src.dpid': n2, 'dst.dpid': n1, 
                'packet_loss': loss, 'delay': delay, 'bandwidth': bw }
        net.link_quality.append(data)

    # Add Controllers
    for i in range(NUM_PARTITION):
        net.addController(f'c{i}', 
                        controller=RemoteController,
                        ip='0.0.0.0', port=OFP_PORT+i)

    # Network required to build before adding controller    
    net.build()
    # ARP must be enable if you want adding flow manually
    net.staticArp()

    # Connect each switch to a different controller
    print('***Add controller to switch')
    for idx, sw_list_id in enumerate(graph_partitions):
        print(sw_list_id)
        for sw_id in sw_list_id:
            print(f'sw_id{sw_id} connected to c{idx}')
            net.get(f's{sw_id+1}').start([net.get(f'c{idx}')])

    net.get('s1').cmdPrint('ovs-vsctl show')
    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    graph: nx.Graph = nx.read_graphml(FILEPATH)
    graph_partitions = part_graph(generate_adjlist(graph), 
                                  num_parts=NUM_PARTITION)
    myNet(graph, graph_partitions)