#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def myNet():
    #OpenDayLight controller
    ODL_CONTROLLER_IP='0.0.0.0'

    #Floodlight controller
    FL_CONTROLLER_IP='0.0.0.0'

    net = Mininet( topo=None, build=False)

    # Create nodes
    h1 = net.addHost( 'h1', mac='01:00:00:00:01:00', ip='192.168.0.1/24' )
    h2 = net.addHost( 'h2', mac='01:00:00:00:02:00', ip='192.168.0.2/24' )

    # Create switches
    s1 = net.addSwitch( 's1', mac='00:00:00:00:00:01' )
    s2 = net.addSwitch( 's2', mac='00:00:00:00:00:02' )

    print("*** Creating links")
    net.addLink(h1, s1)
    net.addLink(h2, s2)   
    net.addLink(s1, s2)  

    # Add Controllers
    odl_ctrl = net.addController( 'c0', controller=RemoteController, ip=ODL_CONTROLLER_IP, port=6633)

    fl_ctrl = net.addController( 'c1', controller=RemoteController, ip=FL_CONTROLLER_IP, port=6634)


    net.build()

    # Connect each switch to a different controller
    s1.start( [odl_ctrl] )
    s2.start( [fl_ctrl] )

    s1.cmdPrint('ovs-vsctl show')

    CLI( net )
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNet()