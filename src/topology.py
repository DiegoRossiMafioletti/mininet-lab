#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch, Host
from mininet.cli import CLI
from mininet.log import setLogLevel, info


def topology():
    net = Mininet(topo=None,
                  build=False,
                  ipBase='10.0.0.0/8')

    info( '*** [topology] Adding controller\n' )
    c0 = net.addController(name='c0',
                           controller=RemoteController,
                           ip='127.0.0.1',
                           protocol='tcp',
                           port=6633)

    info( '*** [topology] Add switches\n')
    s01 = net.addSwitch('s01', cls=OVSKernelSwitch)
    s02 = net.addSwitch('s02', cls=OVSKernelSwitch)
    s03 = net.addSwitch('s03', cls=OVSKernelSwitch)
    s04 = net.addSwitch('s04', cls=OVSKernelSwitch)

    info( '*** [topology] Add hosts\n')
    h11 = net.addHost('h11', cls=Host, ip='10.0.1.1', mac='00:00:00:00:01:01', defaultRoute=None)
    h12 = net.addHost('h12', cls=Host, ip='10.0.1.2', mac='00:00:00:00:01:02', defaultRoute=None)
    h13 = net.addHost('h13', cls=Host, ip='10.0.1.3', mac='00:00:00:00:01:03', defaultRoute=None)
    h21 = net.addHost('h21', cls=Host, ip='10.0.2.1', mac='00:00:00:00:02:01', defaultRoute=None)
    h22 = net.addHost('h22', cls=Host, ip='10.0.2.2', mac='00:00:00:00:02:02', defaultRoute=None)
    h23 = net.addHost('h23', cls=Host, ip='10.0.2.3', mac='00:00:00:00:02:03', defaultRoute=None)
    h31 = net.addHost('h31', cls=Host, ip='10.0.3.1', mac='00:00:00:00:03:01', defaultRoute=None)
    h32 = net.addHost('h32', cls=Host, ip='10.0.3.2', mac='00:00:00:00:03:02', defaultRoute=None)
    h33 = net.addHost('h33', cls=Host, ip='10.0.3.3', mac='00:00:00:00:03:03', defaultRoute=None)
    h41 = net.addHost('h41', cls=Host, ip='10.0.4.1', mac='00:00:00:00:04:01', defaultRoute=None)
    h42 = net.addHost('h42', cls=Host, ip='10.0.4.2', mac='00:00:00:00:04:02', defaultRoute=None)
    h43 = net.addHost('h43', cls=Host, ip='10.0.4.3', mac='00:00:00:00:04:03', defaultRoute=None)

    info( '*** [topology] Add links\n')
    net.addLink(h11, s01)
    net.addLink(h12, s01)
    net.addLink(h13, s01)
    net.addLink(h21, s02)
    net.addLink(h22, s02)
    net.addLink(h23, s02)
    net.addLink(h31, s03)
    net.addLink(h32, s03)
    net.addLink(h33, s03)
    net.addLink(h41, s04)
    net.addLink(h42, s04)
    net.addLink(h43, s04)
    net.addLink(s01, s02)
    net.addLink(s02, s03)
    net.addLink(s03, s04)

    info( '*** [topology] Actually start the network\n')
    net.build()

    info( '*** [topology] Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** [topology] Starting switches\n')
    net.get('s01').start([c0])
    net.get('s02').start([c0])
    net.get('s03').start([c0])
    net.get('s04').start([c0])

    info( '*** [topology] Drop the user in to a CLI so user can run commands\n')
    CLI(net)

    info( '*** [topology] After the user exits the CLI, shutdown the network\n')
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()
