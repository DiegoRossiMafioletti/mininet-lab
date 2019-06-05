from ryu.lib import hub
from operator import attrgetter
from probables import HeavyHitters
from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER


NUM_HITTERS = 3
WINDOW_SIZE = 100
WIDTH = 10
DEPTH = 5

class SketchesMonitor():

    MSG_TPL = 'HEAVY HITTERS of s{}: {}'

    def __init__(self, id, output, window_size=10, num_hitters=5, width=10,
                 depth=0.05):
        self.id = id
        self.output = output
        self.WINDOW_SIZE = window_size
        self.NUM_HITTERS = num_hitters
        self.WIDTH = width
        self.DEPTH = depth
        self.sketch = HeavyHitters(num_hitters=self.NUM_HITTERS,
                                   width=self.WIDTH,
                                   depth=self.DEPTH)
        self.counter = 0

    def add(self,elem):
        self.sketch.add(elem)
        self.counter += 1

        if self.counter == self.WINDOW_SIZE:
            self.report()
            self.counter = 0
            self.sketch.clear()

    def report(self):
        msg = self.MSG_TPL.format(self.id, self.sketch.heavy_hitters)
        self.output.info(msg)


class SimpleMonitor13(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(SimpleMonitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.cms = {}
        self.cms[1] = SketchesMonitor(id=1, output=self.logger,
                                      window_size=WINDOW_SIZE,
                                      num_hitters=NUM_HITTERS,
                                      width=WIDTH, depth=DEPTH)
        self.cms[2] = SketchesMonitor(id=2, output=self.logger,
                                      window_size=WINDOW_SIZE,
                                      num_hitters=NUM_HITTERS,
                                      width=WIDTH, depth=DEPTH)
        self.cms[3] = SketchesMonitor(id=3, output=self.logger,
                                      window_size=WINDOW_SIZE,
                                      num_hitters=NUM_HITTERS,
                                      width=WIDTH, depth=DEPTH)
        self.cms[4] = SketchesMonitor(id=4, output=self.logger,
                                      window_size=WINDOW_SIZE,
                                      num_hitters=NUM_HITTERS,
                                      width=WIDTH, depth=DEPTH)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        body = ev.msg.body

        for stat in sorted([flow for flow in body if flow.priority == 1],
                           key=lambda flow: (flow.match['in_port'],
                                             flow.match['eth_dst'])):
            self.cms[ev.msg.datapath.id].add(stat.match['eth_dst'])
