from ryu.controller.handler import set_ev_cls, MAIN_DISPATCHER
from ryu.controller import ofp_event
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet, ether_types
import time


"""
packet_in_handler
Entra in azione quando uno switch non sa come gestire un pacchetto e lo invia al controller.

1. Arriva un Packet-In: Lo switch non aveva una flow adatta, quindi manda il pacchetto al controller.
2. Il controller legge il pacchetto e recupera:
    → switch che lo ha inviato: dpid
    → porta di ingresso: in_port
    → MAC sorgente: src
    → MAC destinazione: dst
3. Ignora LLDP: Se è traffico utilizzato per la topology discovery, esce subito con return.
4. Controlla i broadcast duplicati: self.seen_broadcasts evita che copie dello stesso broadcast continuino a girare nella topologia.
5. Impara dove si trova l'host sorgente: Se il pacchetto arriva da una porta che non è una porta inter-switch, registra:
    → MAC → switch → porta
    → dentro self.hosts.
6. Guarda se conosce la destinazione. Se non la conosce:
    → destinazione sconosciuta → flooding in modo da riuscire a trovarla.
    → Se invece la conosce: MAC destinazione → switch destinazione → Dijkstra
7. Calcola il percorso: Chiama self.calculate_path(src_switch, dst_switch).
    → Per esempio: 1 → 2 → 4 → 5
8. Trasforma il percorso in porte. Ottiene, per esempio:
    → s1 → porta 2
    → s2 → porta 2
    → s4 → porta 3
    → s5 → porta 1
9. Installa le flow: Per ogni switch del percorso chiama self.add_flow() con una regola del tipo: se eth_dst = MAC destinazione → inoltra su out_port
   Le flow ricevono anche cookie=self.routing_cookie, così potranno essere eliminate in caso di cambio della topologia.
10. Gestisce il pacchetto corrente
    Le nuove flow serviranno soprattutto ai pacchetti successivi. Il pacchetto che ha provocato il Packet-In viene invece inoltrato subito tramite OFPPacketOut.

"""

class PacketHandler:

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
   
        # Messaggio Packet-In ricevuto
        msg = ev.msg

        # Switch che ha inviato il Packet-In
        datapath = msg.datapath

        # DPID dello switch
        dpid = datapath.id

        # Porta dalla quale il pacchetto è entrato nello switch
        in_port = msg.match["in_port"]

        # Analisi del pacchetto ricevuto
        pkt = packet.Packet(msg.data)

        # Estrazione dell'header Ethernet
        eth = pkt.get_protocol(ethernet.ethernet)

        # Ignora i pacchetti LLDP usati per la scoperta della topologia
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        # MAC sorgente e destinazione
        src = eth.src
        dst = eth.dst

        # Controllo dei broadcast duplicati
        if dst == "ff:ff:ff:ff:ff:ff":

            now = time.monotonic()

            broadcast_id = (
                dpid, 
                src,
                hash(bytes(msg.data))
            )

            # Elimina dalla cache i broadcast ormai scaduti

            expired = [
                broadcast
                for broadcast, timestamp in self.seen_broadcasts.items()
                if now - timestamp > self.broadcast_timeout
            ]

            for broadcast in expired:
                del self.seen_broadcasts[broadcast]

            # Se lo stesso frame è già passato su questo switch,
            # significa che è una copia dovuta al flooding

            if broadcast_id in self.seen_broadcasts:
                self.logger.info(
                    "Broadcast già visto su switch %s da %s: scartato",
                    dpid,
                    src
                )
                return

            # Memorizza temporaneamente questo broadcast

            self.seen_broadcasts[broadcast_id] = now


        self.logger.info(
            "Packet-In: switch=%s porta=%s src=%s dst=%s",
            dpid,
            in_port,
            src,
            dst
        )

        if(dpid, in_port) not in self.switch_ports:

            self.hosts[src] = {
                "switch": dpid,
                "port": in_port
            }

            self.logger.info(
                "Host appreso: %s -> switch %s, porta %s",
                src,
                dpid,
                in_port
            )

            self.logger.info(
                "Hosts: %s",
                self.hosts
            )

        # Il modello del Ryu Book apprende proprio l'indirizzo MAC sorgente associandolo alla porta dalla quale il pacchetto è arrivato.
        # Verifica se il MAC destinazione è già conosciuto
        if dst in self.hosts:
            self.logger.info(
                "Destinazione conosciuta: %s → switch %s, porta %s",
                dst,
                self.hosts[dst]["switch"],
                self.hosts[dst]["port"]
            )

            # Switch ai quali sono collegati sorgente e destinazione

            src_switch = self.hosts[src]["switch"]
            dst_switch = self.hosts[dst]["switch"]

            self.logger.info(
                "Calcolo percorso dinamico: switch %s → switch %s",
                src_switch,
                dst_switch
            )

            # Calcolo del percorso dinamico tra i due switch

            path, path_ports = self.calculate_path(src_switch, dst_switch)

            if path is not None:
                path_ports[dst_switch] = self.hosts[dst]["port"]

                self.logger.info(
                    "Porte complete del percorso: %s",
                    path_ports
                )

                out_port = path_ports[dpid]

                self.logger.info(
                    "Switch %s: destinazione %s → porta %s",
                    dpid,
                    dst,
                    out_port
                )

                for switch_id in path:

                    switch_datapath = self.datapaths[switch_id]

                    # Creazione della regola OpenFlow
                    parser = switch_datapath.ofproto_parser

                    out_port = path_ports[switch_id]

                    match = parser.OFPMatch(
                        eth_dst = dst
                    )

                    actions = [
                        parser.OFPActionOutput(out_port)
                    ]

                    # Installazione della regola sullo switch
                    self.add_flow(
                        switch_datapath,
                        1,
                        match,
                        actions,
                        cookie = self.routing_cookie
                    )

                    self.logger.info(
                        "Flow installata: switch %s, dst=%s → porta %s",
                        switch_id,
                        dst,
                        out_port
                    )

                # Inoltro del pacchetto che ha generato il Packet-In
                ofproto = datapath.ofproto
                parser = datapath.ofproto_parser

                out_port = path_ports[dpid]

                actions = [
                    parser.OFPActionOutput(out_port)
                ]

                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=msg.buffer_id,
                    in_port=in_port,
                    actions=actions,
                    data=msg.data
                )

                datapath.send_msg(out)   

        else:
            self.logger.info(
                "Destinazione %s non ancora conosciuta",
                dst
            )



            ofproto = datapath.ofproto # Protocollo OpenFlow utilizzato dal datapath
            parser = datapath.ofproto_parser # Parser dei messaggi OpenFlow

            # Azione: inoltra il pacchetto in flooding
            
            actions = [ 
                parser.OFPActionOutput(ofproto.OFPP_FLOOD)
            ]

            # Se lo switch non ha mantenuto il pacchetto nel buffer, bisogna includere i dati nel Packet-Out

            data = None
            
            if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                data = msg.data

            # Costruzione del messaggio Packet-Out

            out = parser.OFPPacketOut(
                datapath = datapath,
                buffer_id = msg.buffer_id,
                in_port = in_port,
                actions = actions,
                data = data
            )

            datapath.send_msg(out)

