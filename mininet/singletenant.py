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
    s3 = net.addSwitch('s3', cls=OVSKernelSwitch)
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)    
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='172.16.20.10/24', defaultRoute='h1-eth0')
    h2 = net.addHost('h2', cls=Host, ip='172.16.10.10/24', defaultRoute='h2-eth0')
    h3 = net.addHost('h3', cls=Host, ip='192.168.30.10/24', defaultRoute='h3-eth0')

    info( '*** Add links\n')
    net.addLink(s2, s3)
    net.addLink(s2, s1)
    net.addLink(h1, s1)
    net.addLink(h3, s3)
    net.addLink(h2, s2)

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
    s1.cmd('ifconfig s1 172.16.20.1/24')
    s2.cmd('ifconfig s2 172.16.10.1/24')
    s3.cmd('ifconfig s3 192.168.30.1/24')
    
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()