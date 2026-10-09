
# classe topo fornita da Mininet

from mininet.topo import Topo 

# specifica della topologia

class DijkstraTopo(Topo):
    def build(self):

        # host 

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')

        # switch

        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')

        # collegamenti 

        self.addLink(h1, s1)
        self.addLink(s5, h2)

        self.addLink(s1, s2)
        self.addLink(s2, s4)
        self.addLink(s1, s3)
        self.addLink(s3, s4)
        self.addLink(s4, s5)


# il CLI trova la topologia con il nome di dijkstra
# sudo mn --custom mininet/topology.py --topo dijkstra

topos = {
    'dijkstra': lambda: DijkstraTopo()
} 

#  AVVIO
#  sudo mn --custom topology.py --topo dijkstra --controller remote --switch ovsk,protocols=OpenFlow13