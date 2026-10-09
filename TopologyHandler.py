from ryu.controller.handler import set_ev_cls
from ryu.topology import event

"""
Un handler è semplicemente una funzione che Ryu esegue automaticamente quando succede un certo evento.
"""

class TopologyHandler:

    """
    switch_enter_handler
    Ogni qualvolta compaia un nuovo switch:
    1. Prende il suo identificatido dpid;
    2. chiama add_switch
    3. lo aggiunge al grafo
    """

    @set_ev_cls(event.EventSwitchEnter)
    def switch_enter_handler(self, ev): 

        dpid = ev.switch.dp.id
        self.topology_manager.add_switch(dpid)
        self.logger.info(
            "Switch aggiunto: %s",
            dpid
            )
            
        self.logger.info(
            "Grafo: %s",
            self.topology_manager.get_graph()
            )

    """
    link_add_handler
    Ogni qualvolta compaia un collegamento tra due switch:
    1. src → switch di partenza
    2. dst → switch di arrivo
    3. src_port → porta utilizzata da src per andare verso dst
    """

    @set_ev_cls(event.EventLinkAdd)
    def link_add_handler(self, ev):

        link = ev.link
        
        src = link.src.dpid
        dst = link.dst.dpid
        src_port = link.src.port_no

        # Memorizzazione della porta come collegamento verso un altro switch

        self.switch_ports.add((src, src_port))

        self.logger.info(
            "Porte inter-switch: %s",
            self.switch_ports
        )
        
        self.topology_manager.add_link(
            src,
            dst,
            src_port
            )
            
        self.logger.info(
            "Link aggiunto: %s -> %s, porta %s",
            src,
            dst,
            src_port
            )

        self.logger.info(
            "Grafo: %s",
            self.topology_manager.get_graph()
            )

    """
    link_delete_handler
    Ogni qualvolta scompaia un nuovo collegamento:
    1. remove_link lo elimina dal grafo
    2. switch_port_discard elimina quella porta dall'elenco delle porta inter-switch
    3. delete_routing_flows cancella le vecchie flow di routing
    """

    @set_ev_cls(event.EventLinkDelete)
    def link_delete_handler(self, ev):
        
        link = ev.link

        src = link.src.dpid
        dst = link.dst.dpid
        src_port = link.src.port_no

        # Rimozione del link dal grafo
        self.topology_manager.remove_link(
            src,
            dst
        )

        # La porta non è più considerata inter-switch
        self.switch_ports.discard(
            (src, src_port)
        )

        self.logger.info(
            "Link rimosso: %s -> %s, porta %s",
            src,
            dst,
            src_port
        )

        self.logger.info(
            "Grafo aggiornato: %s",
            self.topology_manager.get_graph()
        )

        self.delete_routing_flows()

