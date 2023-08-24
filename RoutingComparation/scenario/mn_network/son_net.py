from mininet.topo import Topo
from mininet.net import Mininet

from mininet.cli import CLI
from mininet.node import RemoteController, OVSSwitch


from mininet.log import setLogLevel

import uvicorn
from mn_restapi.mn_restapi_hook import RestHookMN

import argparse
import random
argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="resthookmn startup rest api port")
argParser.add_argument("openflow_port", type=int, default=6653, help="open flow connect port")
args = argParser.parse_args()

# Number of switches and hosts
NUM_SWITCHES = 35
NUM_HOSTS = 35

# List to store switches and hosts
switches = []
hosts = []

RESTHOOKMN_PORT = args.rest_port
OFP_PORT = args.openflow_port

class MyTopo(Topo):
    def build(self):
        for i in range(NUM_SWITCHES):
            s = self.addSwitch('s' + str(i))
            switches.append(s)
        
        for i in range(NUM_HOSTS):
            h = self.addHost('h' + str(i))
            hosts.append(h)
            
        # Shuffle the swithes and hosts 
        random.shuffle(switches)    
        random.shuffle(hosts)
        
        # Connect switches randomly
        for i in range(NUM_SWITCHES - 1):
            self.addLink(switches[i], switches[i+1])
        
        # Connect hosts to switch
        for i in range(NUM_HOSTS):
            self.addLink(hosts[i], switches[i])


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
    
    app = RestHookMN(net=net)
    uvicorn.run(app, host="0.0.0.0", port=RESTHOOKMN_PORT)
    CLI(net)
    net.stop()