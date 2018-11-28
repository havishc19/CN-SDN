#!/usr/bin/python

from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch
from mininet.topo import Topo

class customTopo(Topo):

    "Custom Topology"

    def __init__(self):

        Topo.__init__(self)

        #Add hosts
        h1 = self.addHost('h1', cls=Host, ip='10.0.0.1', defaultRoute=None)
        h2 = self.addHost('h2', cls=Host, ip='10.0.0.2', defaultRoute=None)
        h4 = self.addHost('h4', cls=Host, ip='10.0.0.4', defaultRoute=None)
        h3 = self.addHost('h3', cls=Host, ip='10.0.0.3', defaultRoute=None)

        #Add switches
        s3 = self.addSwitch('s3', cls=OVSKernelSwitch)
        s1 = self.addSwitch('s1', cls=OVSKernelSwitch)
        s2 = self.addSwitch('s2', cls=OVSKernelSwitch)
        s4 = self.addSwitch('s4', cls=OVSKernelSwitch)
        s5 = self.addSwitch('s5', cls=OVSKernelSwitch)

        #Add links
        self.addLink(h1, s4)
        self.addLink(h2, s4)
        self.addLink(h3, s5)
        self.addLink(h4, s5)

        self.addLink(s4, s2)
        self.addLink(s4, s3)
        self.addLink(s5, s2)
        self.addLink(s5, s3)

        self.addLink(s1, s3)
        self.addLink(s1, s2)

topos = { 'mytopo': (lambda: customTopo() ) }
