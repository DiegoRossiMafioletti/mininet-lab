from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0

from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types


class L2Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L2Switch, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.port = {}

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        dp = msg.datapath
        ofp = dp.ofproto
        ofp_parser = dp.ofproto_parser
        
        # inicializa o dicionario
        self.port.setdefault(dp.id, {})

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        # ignora pacotes lldp
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        
        # associa a porta de origem ao dicionario
        self.port[dp.id][eth.src] = msg.in_port

        self.logger.info("eth type: %#04x", eth.ethertype)
        self.logger.info("datapath: %016x", dp.id)
        self.logger.info("src mac: %s", eth.src)
        self.logger.info("src port: %s", msg.in_port)
        self.logger.info("dst mac: %s", eth.dst)
        if eth.dst in self.port[dp.id]:
            self.logger.info("dst port: %s", self.port[dp.id][eth.dst])
        
        self.logger.info("\neth packet:\n %s", eth)
        self.logger.info("msg packet:\n %s", msg)
        
        actions = [ofp_parser.OFPActionOutput(ofp.OFPP_FLOOD)]
        out = ofp_parser.OFPPacketOut(
            datapath=dp, buffer_id=msg.buffer_id, in_port=msg.in_port, actions=actions)
        dp.send_msg(out)


    @set_ev_cls(ofp_event.EventOFPStateChange,[MAIN_DISPATCHER, DEAD_DISPATCHER])
    def state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.info('datapath conectado: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info('datapath desconectado: %016x', datapath.id)
                del self.datapaths[datapath.id]
