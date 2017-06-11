from mininet.topo import Topo

# Warning: this topology will not work for now, because it has loops in the links between switches.
# TODO: Make this topology work with the Ryu controller.
class TripleSwitchTopo(Topo):
    
    def __init__(self):
        # Initialize topology
        Topo.__init__(self)

        # Add hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')

        # Add switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        # Add links
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        
        self.addLink(h3, s2)

        self.addLink(h4, s3)
        self.addLink(h5, s3)
        
        self.addLink(s1, s2)
        self.addLink(s1, s3)
        self.addLink(s2, s3)

topos = { 'tripleswitch': (lambda: TripleSwitchTopo()) }
