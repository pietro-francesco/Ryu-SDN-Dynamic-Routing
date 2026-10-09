from ryu.controller.handler import set_ev_cls, CONFIG_DISPATCHER
from ryu.controller import ofp_event

"""
Modulo che gestisce le regole di openflow sugli switch.

1. table-miss: se lo switch non sa come procedere per invio. chiede al controller
2. add_flow: lo switch ha installate le regole per inviare il pacchetto su una determinata porta
3. delete_routing_flows: se cambia la topologia, disinstalla le vecchie regole
"""

class FlowService:


    """
    switch_features_handler
    Viene eseguito ogni volta che uno switch si collega al controller, fa due cose:
    1. salva lo switch in self.datapaths così il controller può ricontattarlo
    2. installa la table-miss con priorità 0 → Se non si ha una regola per un determinato pacchetto, lo si manda la controller.
    """

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        datapath = ev.msg.datapath

        # Memorizzazione del datapath dello switch
        self.datapaths[datapath.id] = datapath

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(
            datapath,
            0,
            match,
            actions
        )

    """
    add.flow
    Installare una regola su uno switch.
    Riceve:
    1. datapath → su quale switch installarla
    2. priority → quanto è importante la regola
    3. match → quali pacchetti devono corrispondere
    4. actions → cosa deve fare lo switch
    5. cookie → etichetta che identifica la flow

    add_flow traduce la decisione del controller su un determinato invio e la installa nello switch con datapath.send_msg(flow_mod)
    """

    def add_flow(self, datapath, priority, match, actions, cookie=0):

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        flow_mod = parser.OFPFlowMod(
            datapath = datapath,
            priority = priority,
            match = match,
            instructions = instructions,
            cookie = cookie
        )

        datapath.send_msg(flow_mod)

    """
    delete_routing_flows
    Fa l'operazione opposta di add_flow, quando cade un link, le vecchie regole installate potrebbero non essere più valide.
    
    1. attraversa tutti gli switch contenuti in self.datapaths;
    2. cerca le flow contrassegnate con self.routing_cookie;
    3. invia un comando OpenFlow di cancellazione.
    """

    def delete_routing_flows(self):

        for datapath in self.datapaths.values():

            ofproto = datapath.ofproto
            parser = datapath.ofproto_parser

            flow_mod = parser.OFPFlowMod(
                datapath=datapath,
                cookie=self.routing_cookie,
                cookie_mask=0xFFFFFFFFFFFFFFFF,
                table_id=0,
                command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY,
                match=parser.OFPMatch()
            )

            datapath.send_msg(flow_mod)

        self.logger.info(
            "Flow di routing obsolete eliminate"
        )