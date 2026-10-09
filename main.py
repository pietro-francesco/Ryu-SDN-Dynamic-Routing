from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3

# TopologyManager costruisce e mantiene il grafo della rete
from topology_manager import TopologyManager

from PacketHandler import PacketHandler
from TopologyHandler import TopologyHandler

from flow_service import FlowService
from routing_services import RoutingService

class DijkstraController(
    app_manager.RyuApp,
    PacketHandler,
    TopologyHandler,
    FlowService,
    RoutingService
):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # __init__: Creo il TopologyManager che conserverà il grafo scoperto da Ryu. 
    # parte il controller → crea TopologyManager → All'avvio il grafo è vuoto → inizialmente graph = {}

    def __init__(self, *args, **kwargs):
        super(DijkstraController, self).__init__(*args, **kwargs)

        self.topology_manager = TopologyManager()
        self.hosts = {}
        self.switch_ports = set()
        self.seen_broadcasts = {}
        self.datapaths = {}
        # Durata della cache dei broadcast
        self.broadcast_timeout = 2.0
        self.routing_cookie = 0x1