#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    h1s1 = net.addHost('h1s1', cls=Host, defaultRoute='h1s1-eth0')
    h2s1 = net.addHost('h2s1', cls=Host, defaultRoute='h2s1-eth0')    
    h1s2 = net.addHost('h1s2', cls=Host, defaultRoute='h1s2-eth0')
    h2s2 = net.addHost('h2s2', cls=Host, defaultRoute='h2s2-eth0')
    h1s3 = net.addHost('h1s3', cls=Host, defaultRoute='h1s3-eth0')
    h2s3 = net.addHost('h2s3', cls=Host, defaultRoute='h2s3-eth0')    

    info( '*** Add links\n')
    net.addLink(s1, s2)
    net.addLink(s3, s2)
    net.addLink(h1s1, s1)
    net.addLink(h2s1, s1)
    net.addLink(s2, h1s2)
    net.addLink(s2, h2s2)
    net.addLink(h1s3, s3)
    net.addLink(h2s3, s3)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([c0])
    net.get('s2').start([c0])
    net.get('s3').start([c0])

    info( '*** Post configure switches and hosts\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

