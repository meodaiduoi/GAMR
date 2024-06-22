
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

from mn_restapi.mn_hook_util import * 
from mn_restapi.mn_restapi_hook import *
import uvicorn

import argparse
argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")
argParser.add_argument("openflow_port", type=int, default=6653, help="open flow connect port")
args = argParser.parse_args()

RESTHOOKMN_PORT = args.rest_port
OFP_PORT = args.openflow_port

import random
# set random state of script
random.seed(69)

class MyTopo(Topo):
    def build(self):        
        device_num = 20
        swlist = []
        for i in range(1, device_num):
            swlist.append(self.addSwitch(f's{i}', stp=True))
        
        hlist = []
        for i in range(1, device_num):
            hlist.append(self.addHost(f'h{i}', mac=int_to_mac(i)))
 
        for (d1, d2) in zip(swlist, hlist):
            self.addLink(d1, d2)

        # add switches and hosts
        for (sw, h) in zip(swlist, hlist):
            self.addLink(sw, h, bw=500, delay='1ms', max_queue_size=1000, loss=0, use_htb=True)
        
        # add linear path between switches
        for i in range(len(swlist) - 1):
            loss = random.randint(1, 3)
            delay = random.randint(5, 10)
            bw = random.randint(50, 100)
            self.addLink(swlist[i], swlist[i+1], bw=bw, delay=f'{delay}ms', max_queue_size=1000, loss=loss, use_htb=True)
               
        for d1 in swlist:
            for d2 in reversed(swlist):
                # check if link between 2 nodes not exist and not connected to itself
                if not link_exist(self, d1, d2) and d1 != d2:
                    if random.random() < 0.10:
                        loss = random.randint(3, 7)
                        delay = random.randint(10, 25)
                        self.addLink(d1, d2, bw=50, delay=f'{delay}ms',  max_queue_size=1000, loss=loss, use_htb=True)
                
if __name__ == '__main__':
    setLogLevel( 'info' )
    # add ccontroller and build the network
    c0 = RemoteController('c0', ip='0.0.0.0')
    net = Mininet(topo=MyTopo(), 
                  controller=c0,
                  switch=OVSSwitch,
                  link=TCLink,
                  ipBase='10.0.0.0/24')
    
    # ARP must be enable if you want adding flow manually
    net.staticArp()
    net.start()

    # enable_stp(net)
    # wait_for_stp(net)
    
    app = RestHookMN(net=net)
    uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
    CLI(net)
    net.stop()