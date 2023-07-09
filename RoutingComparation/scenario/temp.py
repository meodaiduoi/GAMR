#!/home/onos/Desktop/bknet/venv11/bin/python3.11

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

class MyTopo( Topo ):
    def __init__( self ):
        Topo.__init__( self )
        h1 = self.addHost( 'h1' )
        h2 = self.addHost( 'h2' )
        switch = self.addSwitch( 's1' )
        self.addLink( h1, switch )
        self.addLink( h2, switch )

if __name__ == '__main__':
    setLogLevel( 'info' )
    topo = MyTopo()
    net = Mininet( topo=topo )
    h1 = net.getNodeByName('h1')
    h2 = net.getNodeByName('h2')
    result = net.ping([h1, h2])
    print(f'result: {result}')    

    net.stop()
