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
    s2 = net.addSwitch('s2', cls=OVSKernelSwitch)
    r4 = net.addHost('r4', cls=Node, ip='0.0.0.0')
    r4.cmd('sysctl -w net.ipv4.ip_forward=1')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch)
    r3 = net.addHost('r3', cls=Node, ip='0.0.0.0')
    r3.cmd('sysctl -w net.ipv4.ip_forward=1')

    info( '*** Add hosts\n')
    h1 = net.addHost('h1', cls=Host, ip='10.0.1.10/24', defaultRoute='10.0.1.3')
    h2 = net.addHost('h2', cls=Host, ip='10.0.2.10/24', defaultRoute='10.0.2.4')

    info( '*** Add links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s2)
    net.addLink(s1, r3)
    net.addLink(s1, r4)
    net.addLink(s2, r3)
    net.addLink(s2, r4)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s2').start([c0])
    net.get('s1').start([c0])

    info( '*** Post configure switches and hosts\n')
    r3.cmd('ifconfig r3-eth0 10.0.1.3 netmask 255.255.255.0')
    r3.cmd('ifconfig r3-eth1 10.0.2.3 netmask 255.255.255.0')
    r4.cmd('ifconfig r4-eth0 10.0.1.4 netmask 255.255.255.0')
    r4.cmd('ifconfig r4-eth1 10.0.2.4 netmask 255.255.255.0')

    s1.cmd('sh ovs-vsctl set bridge s1 protocols=OpenFlow13')
    s2.cmd('sh ovs-vsctl set bridge s2 protocols=OpenFlow13')

    s1.intf('s1-eth1').setMAC('00:00:00:00:01:01')
    s1.intf('s1-eth2').setMAC('00:00:00:00:01:02')
    s1.intf('s1-eth3').setMAC('00:00:00:00:01:03')

    s2.intf('s2-eth1').setMAC('00:00:00:00:02:01')
    s2.intf('s2-eth2').setMAC('00:00:00:00:02:02')
    s2.intf('s2-eth3').setMAC('00:00:00:00:02:03')

    r3.intf('r3-eth0').setMAC('00:00:00:00:03:01')
    r3.intf('r3-eth1').setMAC('00:00:00:00:03:02')
    
    r4.intf('r4-eth0').setMAC('00:00:00:00:04:01')
    r4.intf('r4-eth1').setMAC('00:00:00:00:04:02')

    h1.intf('h1-eth0').setMAC('00:00:00:00:00:01')
    h2.intf('h2-eth0').setMAC('00:00:00:00:00:02')

    h1.cmd('ip route add default via 10.0.1.3')
    h2.cmd('ip route add default via 10.0.2.4')


    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

