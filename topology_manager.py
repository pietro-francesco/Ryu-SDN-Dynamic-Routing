"""
topology_manager.py

Memorizza la topologia della rete. Mentre Ryu scopre la rete, topology_manager la memorizza e dijkstra usa quella rappresentazione per calcolarei l percorso.

1. self.graph = {} → contiene la rappresentazione della rete.
2. add_switch(dpid) → aggiunge uno switch al grafo, se non esiste già.
3. add_link(src, dst, src_port, cost=1) → registra che da src posso raggiungere dst, usando src_port, con un certo cost.
4. remove_link(src, dst) → elimina quel collegamento quando il link cade.
5. get_graph() → restituisce il grafo aggiornato agli altri componenti, soprattutto al routing/Dijkstra.

"""


class TopologyManager:
    def __init__(self):
        self.graph = {}

    def add_switch(self, dpid):
        # Metodo per registrare uno switch
        if dpid not in self.graph:
            self.graph[dpid] = {}
            
    def add_link(self, src, dst, src_port, cost=1):
        # Metodo per registrare un link
        self.add_switch(src)
        self.add_switch(dst)
        
        self.graph[src][dst] = {
            "port": src_port,
            "cost": cost
            }

    def remove_link(self, src, dst):
        if src in self.graph and dst in self.graph[src]:
            del self.graph[src][dst]

    def get_graph(self):
        # Restituisce il grafo
        return self.graph