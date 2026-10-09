# dijkstra() riceve il grafo e calcola percorso minimo e costo
from dijkstra import dijkstra

"""
RoutingService
Fa da ponte tra Dijkstra e il forwarding OpenFlow
"""

class RoutingService:

    """
    calculate_path
    Trova il percorso migliore tra lo switch sorgente e quello di destinazione:
    1. prende il grafo aggiornato da TopologyManager con get_graph();
    2. passa a dijkstra() il grafo, lo switch sorgente e quello destinazione;
    3. Dijkstra restituisce, per esempio, path = [1, 2, 4, 5] e cost = 3;
    4. a quel punto chiama get_path_port() per trasformare quel percorso in porte reali degli switch.
    """

    def calculate_path(self, source, destination):

        graph = self.topology_manager.get_graph()

        path, cost = dijkstra(
            graph,
            source,
            destination
        )

        self.logger.info(
            "Percorso minimo: %s",
            path
        )

        self.logger.info(
            "Costo totale: %s",
            cost
        )

        # Se Dijkstra ha trovato un percorso, ricava le porte da utilizzare

        if path is not None:
            path_ports = self.get_path_port(path)

            return path, path_ports
        
        return None, None

    """
    get_path_port
    Trasforma il percorso trovato in porte di uscita da utilizzare su ogni switch
    """

    def get_path_port(self, path):

        graph = self.topology_manager.get_graph()

        path_ports = {}

        for i in range(len(path)-1):
            current_switch = path[i]
            next_switch = path[i+1]

            out_port = graph[current_switch][next_switch]["port"]

            path_ports[current_switch] = out_port

            self.logger.info(
                "Switch %s -> Switch %s : porta di uscita %s",
                current_switch,
                next_switch,
                out_port
            )
        
        return path_ports