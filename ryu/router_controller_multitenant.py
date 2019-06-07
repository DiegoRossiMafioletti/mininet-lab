# Copyright (C) 2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import icmp
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib.packet import vlan
from ryu.lib.packet import ether_types
import os
import string
import subprocess
from time import sleep
from netaddr import IPNetwork, IPAddress


class RouterController(app_manager.RyuApp):

	def __init__(self, *args, **kwargs):
		super(RouterController,self).__init__(*args,**kwargs)									
		self.netmask = '255.255.255.0'
		#inicializa a tabela arp	
		self.mac_table = {}
		self.routing_table = {}
		self.mac_switches = {1:{'mac':'0a:0a:0a:0a:0a:0a'}, 2:{'mac':'0b:0b:0b:0b:0b:0b'}, 3:{'mac':'0c:0c:0c:0c:0c:0c'}}
		self.portas_switches = {}
		self.ip_switches = {1:{'ip':'172.16.10.50'}, 2:{'ip':'192.168.30.50'}, 3:{'ip':'172.16.20.50'}}

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def switch_features_handler(self, ev):
		datapath = ev.msg.datapath
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		msg = ev.msg
	
		#verifica o numero de portas
		self.send_port_stats_request(datapath)
		match = parser.OFPMatch()
		actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
		self.add_flow(datapath, 0, match, actions)

	#Adiciona um flow na tabela de flows do Switch OpenFlow
	def add_flow(self, datapath, priority, match, actions):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		# construct flow_mod message and send it.
		inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
		mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
		datapath.send_msg(mod) 

	@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
	def _packet_in_handler(self, ev):
	
		msg = ev.msg		
		in_port = msg.match['in_port']		
		datapath = msg.datapath		
		dpid = datapath.id		
		self.ip_switches.setdefault(dpid, {})
		self.mac_switches.setdefault(dpid,{})

		#analisa o pacote recebido usando a biblioteca de pacotes
		pkt = packet.Packet(msg.data)
		eth_pkt = pkt.get_protocol(ethernet.ethernet)
		pkt_icmp = pkt.get_protocol(icmp.icmp)
		pkt_vlan = pkt.get_protocol(vlan.vlan)
		
		#define o valor padrao para o dicionario
		if not eth_pkt:
			return
		if eth_pkt:
			if (eth_pkt.dst == '00:00:00:00:00:00') and (eth_pkt.src=='00:00:00:00:00:00'):
				if 'ports' in self.ip_switches[dpid]:
					if in_port not in self.ip_switches[dpid]['ports']:
						(self.ip_switches[dpid]['ports']).append(in_port)
				else:
					self.ip_switches[dpid]['ports'] = []
					(self.ip_switches[dpid]['ports']).append(in_port)			

		pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
		if pkt_icmp:

			self._handle_icmp(datapath, in_port, eth_pkt, pkt_ipv4, pkt_icmp, pkt,msg)
			return

		if pkt_ipv4:		
						
			return		
		pkt_arp = pkt.get_protocol(arp.arp)
		if pkt_arp:
			self._handle_arp(msg, datapath, in_port, eth_pkt, pkt_arp, pkt_vlan)
			return
		if pkt_vlan:

			return
	"""
	Processa os pacotes arp
	"""
	def _handle_arp(self, msg, datapath, in_port, eth_pkt, pkt_arp, pkt_vlan):
		
		dpid = datapath.id
		self.mac_table.setdefault(pkt_arp.src_ip,{})
		if(pkt_arp.opcode == arp.ARP_REPLY):			
			if pkt_arp.dst_ip == self.ip_switches[dpid]['ip']:				
				self.mac_table[pkt_arp.src_ip]['mac'] = pkt_arp.src_mac
				self.routing_table.setdefault(dpid, {})
				self.routing_table[dpid][pkt_arp.src_ip] = in_port			
			
			return
		self.mac_table[pkt_arp.src_ip]['mac'] = pkt_arp.src_mac
		self.routing_table.setdefault(dpid, {})
		
		self.routing_table[dpid][pkt_arp.src_ip] = in_port
		pkt_src_ip = pkt_arp.src_ip
		pkt_dst_ip = pkt_arp.dst_ip
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser		
		dst = eth_pkt.dst
		src = eth_pkt.src
		#Se o arp request for endereçado ao switch
		if pkt_dst_ip == self.ip_switches[dpid]['ip']:						
			pkt = packet.Packet()
			pkt.add_protocol(ethernet.ethernet(ethertype=eth_pkt.ethertype, dst=eth_pkt.src, src=self.mac_switches[dpid]['mac'] ))			
			pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY, src_mac=self.mac_switches[dpid]['mac'], src_ip=self.ip_switches[dpid]['ip'], dst_mac=pkt_arp.src_mac, dst_ip=pkt_arp.src_ip))			
			out_port = in_port			
			actions = [parser.OFPActionOutput (port=out_port)]
			match = parser.OFPMatch(eth_type = ether_types.ETH_TYPE_ARP, eth_dst=eth_pkt.src)
			self.add_flow(datapath, 2, match, actions)
			self._send_packet(datapath, in_port, out_port, pkt, actions)
	
		else:
			#se estiver na mesma sub rede, fazer broadcast
			

			pkt = packet.Packet()
			pkt.add_protocol(ethernet.ethernet(ethertype=eth_pkt.ethertype, 
							dst=eth_pkt.src, src=self.mac_switches[dpid]['mac']))
			
			pkt.add_protocol(vlan.vlan(pcp=pkt_vlan.pcp, cfi=pkt_vlan.cfi,vid=pkt_vlan.vid, ethertype=pkt_vlan.ethertype))

			pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY, 
							src_mac=pkt_arp.dst_mac, 
							src_ip=pkt_arp.dst_ip, 
							dst_mac=pkt_arp.src_mac, 
							dst_ip=pkt_arp.src_ip))

			match = parser.OFPMatch(eth_dst=eth_pkt.src)
			actions = [parser.OFPActionOutput (port=in_port)]
			self.add_flow(datapath, 2, match, actions)

			if(pkt_arp.opcode!=arp.ARP_REPLY):
				pkt.serialize()
				data = pkt.data					
				out = parser.OFPPacketOut(datapath=datapath, 
											buffer_id=ofproto.OFP_NO_BUFFER,
											in_port=ofproto.OFPP_CONTROLLER, 
											actions=actions,
											data=data)
				
				datapath.send_msg(out)

				
	"""
	Processa os pacotes ICMP
	"""	
	def _handle_icmp(self, datapath, port, pkt_eth, pkt_ipv4, pkt_icmp, pkt_orig, msg):
		dst = pkt_eth.dst
		src = pkt_eth.dst
		dpid = datapath.id
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser		
		self.routing_table.setdefault(dpid,{})
		self.routing_table[dpid][pkt_ipv4.src] = port

		if pkt_ipv4.dst == self.ip_switches[dpid]['ip']:
			
			port = ofproto.OFPP_CONTROLLER
			actions = [parser.OFPActionOutput (port=port)]
			pkt = packet.Packet()			
			pkt.add_protocol(ethernet.ethernet(ethertype=pkt_eth.ethertype,dst=pkt_eth.src,src=self.mac_switches[dpid]['mac']))
			pkt.add_protocol(ipv4.ipv4(dst=pkt_ipv4.src,src=self.ip_switches[dpid]['ip'],proto=pkt_ipv4.proto, option=None))
			pkt.add_protocol(icmp.icmp(type_=icmp.ICMP_ECHO_REPLY,code=icmp.ICMP_ECHO_REPLY_CODE,csum=0,data=pkt_icmp.data))
			match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst = pkt_ipv4.dst)
			self.add_flow(datapath, 2, match, actions)	
			self._send_packet(datapath,port,pkt,actions)
		else:
			#Se os ips src e do switch se encontram na mesma subnet			
			if self.same_subnet(pkt_ipv4.dst, self.ip_switches[dpid]['ip']):	
				#PEGAR PORTAS PARA HOSTS DO SWITCH				
				broadcast_ports = list(set(self.portas_switches[dpid]['allports']) - set(self.ip_switches[dpid]['ports']))				
				#verifica se esta na tabela arp
				if pkt_ipv4.dst in self.mac_table:					
					mac_dest = self.mac_table[pkt_ipv4.dst]['mac']
					mac_src = self.mac_table[pkt_ipv4.src]['mac']
					out_port = self.routing_table[dpid][pkt_ipv4.dst]			 
					pkt_orig.serialize()		
					data = pkt_orig.data

					match_entrada = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,											
											ipv4_dst=pkt_ipv4.src)

					actions = [parser.OFPActionSetField(eth_dst=mac_src),
								parser.OFPActionSetField(eth_src=mac_dest),										
										parser.OFPActionOutput (port=port)]
			
					self.add_flow(datapath, 3, match_entrada, actions)


					match_saida = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,											
											ipv4_dst=pkt_ipv4.dst)

					actions = [parser.OFPActionSetField(eth_dst=mac_dest),
								parser.OFPActionSetField(eth_src=mac_src),										
										parser.OFPActionOutput (port=out_port)]

					out = parser.OFPPacketOut(datapath=datapath, 
													buffer_id=ofproto.OFP_NO_BUFFER,
													in_port=port, 
													actions=actions,
													data=data)
					self.add_flow(datapath, 3, match_saida, actions)
					datapath.send_msg(out)

				else:					
					pkt = packet.Packet()
					mac_dest = 'ff:ff:ff:ff:ff:ff'
					pkt.add_protocol(ethernet.ethernet(ethertype=ether_types.ETH_TYPE_ARP, dst=mac_dest, src=self.mac_switches[dpid]['mac']))
					pkt.add_protocol(arp.arp(opcode=arp.ARP_REQUEST, src_mac = self.mac_switches[dpid]['mac'], src_ip = self.ip_switches[dpid]['ip'],
					     					dst_mac=mac_dest,
											dst_ip = pkt_ipv4.dst))
					pkt.serialize()
					data = pkt.data
					match_saida = parser.OFPMatch(in_port=port, eth_type=ether_types.ETH_TYPE_IP, ipv4_dst=pkt_ipv4.dst)
					
					for out_port in broadcast_ports:
						if out_port != port:					

							actions = [parser.OFPActionOutput (port=out_port)]
							
							out = parser.OFPPacketOut(datapath=datapath, 
									buffer_id=ofproto.OFP_NO_BUFFER,
									in_port=port, 
									actions=actions,
									data=data)
							
							datapath.send_msg(out)		
					
			else:
				broadcast_ports = list(set(self.portas_switches[dpid]['allports']) - set(self.ip_switches[dpid]['ports']))								
				if pkt_icmp.type == icmp.ICMP_ECHO_REPLY:
					if pkt_ipv4.dst in self.routing_table:						
						mac_dest = self.mac_table[pkt_ipv4.dst]['mac']
						mac_src = self.mac_table[pkt_ipv4.src]['mac']
						out_port = self.routing_table[dpid][pkt_ipv4.dst]
						match_saida = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,											
												ipv4_dst=pkt_ipv4.dst)

						actions = [parser.OFPActionOutput (port=out_port)]

						out = parser.OFPPacketOut(datapath=datapath, 
													buffer_id=ofproto.OFP_NO_BUFFER,
													in_port=port, 
													actions=actions,
													data=data)
							
						self.add_flow(datapath, 3, match_saida, actions)
						
						return 
					else:
						for out_port in self.ip_switches[dpid]['ports']:
							if out_port != port:
								mac_dest = self.mac_table[pkt_ipv4.dst]['mac']
								pkt_orig.serialize()
								data = pkt_orig.data								

								
								match_saida = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,											
												ipv4_dst=pkt_ipv4.dst)

								actions = [parser.OFPActionSetField(eth_dst=mac_dest),
											parser.OFPActionOutput (port=out_port)]
							
								out = parser.OFPPacketOut(datapath=datapath, 
																buffer_id=ofproto.OFP_NO_BUFFER,
																in_port=port, 
																actions=actions,
																data=data)
								self.add_flow(datapath, 3, match_saida, actions)
								datapath.send_msg(out)

								
								match_entrada = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,											
												ipv4_dst=pkt_ipv4.src)
															
								actions = [parser.OFPActionSetField(eth_dst=mac_src),
											parser.OFPActionOutput (port=port)]
						
								out = parser.OFPPacketOut(datapath=datapath, 
																buffer_id=ofproto.OFP_NO_BUFFER,
																in_port=out_port, 
																actions=actions,
																data=data)
								self.add_flow(datapath, 3, match_entrada, actions)
						

				else:
					if pkt_ipv4.dst in self.routing_table:						
						mac_dest = self.mac_table[pkt_ipv4.dst]['mac']
						out_port = self.routing_table[dpid][pkt_ipv4.dst]										
	
						match_saida = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,											
											ipv4_dst=pkt_ipv4.dst)

						actions = [parser.OFPActionOutput (port=out_port)]

						out = parser.OFPPacketOut(datapath=datapath, 
													buffer_id=ofproto.OFP_NO_BUFFER,
													in_port=port, 
													actions=actions,
													data=data)
						self.add_flow(datapath, 3, match_saida, actions)
						datapath.send_msg(out)
					else:	
						for out_port in self.ip_switches[dpid]['ports']:
							if out_port != port:
								
								mac_src = self.mac_table[pkt_ipv4.src]['mac']
								pkt_orig.serialize()
								data = pkt_orig.data								

								
								match_saida = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,											
												ipv4_dst=pkt_ipv4.src)

								actions = [parser.OFPActionSetField(eth_dst=mac_src),
									parser.OFPActionOutput (port=port)]
							
								out = parser.OFPPacketOut(datapath=datapath, 
																buffer_id=ofproto.OFP_NO_BUFFER,
																in_port=out_port, 
																actions=actions,
																data=data)
								self.add_flow(datapath, 4, match_saida, actions)
															
								match_entrada = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP,											
												ipv4_dst=pkt_ipv4.dst)
															
								actions = [parser.OFPActionOutput (port=out_port)]
						
								out = parser.OFPPacketOut(datapath=datapath, 
																buffer_id=ofproto.OFP_NO_BUFFER,
																in_port=port, 
																actions=actions,
																data=data)
								self.add_flow(datapath, 3, match_entrada, actions)
								datapath.send_msg(out)								
				
	def _send_packet(self, datapath, in_port, out_port, pkt, actions):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		pkt.serialize()
		data = pkt.data		
		out = parser.OFPPacketOut(datapath=datapath, 
									buffer_id=ofproto.OFP_NO_BUFFER,
									in_port=in_port, 
									actions=actions,
									data=data)
		
		datapath.send_msg(out)
	def foward_packet(self, datapath, port, pkt, pkt_ipv4):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser
		pkt.serialize()		
		data = pkt.data
		actions = [parser.OFPActionOutput (port=port)]
		
		#pacotes dp tipo ip
		#match = parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IP, ipv4_dst = pkt_ipv4.dst)
		#self.add_flow(datapath, 3, match, actions)

		out = parser.OFPPacketOut(datapath=datapath, 
									buffer_id=ofproto.OFP_NO_BUFFER,
									in_port=ofproto.OFPP_CONTROLLER, 
									actions=actions,
									data=data)
		datapath.send_msg(out)

	def _send_packet_v2(self, datapath, port, pkt, eth_pkt):
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser		
		pkt.serialize()
		data = pkt.data
		actions = [parser.OFPActionOutput (port=port)]
		match = parser.OFPMatch(eth_dst=eth_pkt.src)
		self.add_flow(datapath, 1, match, actions)
		out = parser.OFPPacketOut(datapath=datapath, 
									buffer_id=ofproto.OFP_NO_BUFFER,
									in_port=ofproto.OFPP_CONTROLLER, 
									actions=actions,
									data=data)
		
		datapath.send_msg(out)
	
	def send_port_stats_request(self, datapath):
		ofp = datapath.ofproto
		ofp_parser = datapath.ofproto_parser
		req = ofp_parser.OFPPortStatsRequest(datapath, 0, ofp.OFPP_ANY)
		datapath.send_msg(req)

	@set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
	def port_stats_reply_handler(self, ev):
		datapath = ev.msg.datapath
		dpid = datapath.id
		ports = []
		self.portas_switches.setdefault(dpid,{})
		for stat in ev.msg.body:
			ports.append(stat.port_no)
		ports = ports[1:]
		for port in ports:
			if 'allports' in self.portas_switches[dpid]:
				if port not in self.portas_switches[dpid]['allports']:
					(self.portas_switches[dpid]['allports']).append(port)
			else:
				self.portas_switches[dpid]['allports'] = []
				(self.portas_switches[dpid]['allports']).append(port)
			self.send_arp_pkt(datapath, 0)
	
	def same_subnet(self, pkt_dst_ip, router_ip):
		ip_rede = router_ip+"/24"
		return IPAddress(pkt_dst_ip) in IPNetwork(ip_rede)

	def send_arp_pkt(self,datapath, in_port):
		
		pkt = packet.Packet()
		pkt.add_protocol(ethernet.ethernet(ethertype=ether_types.ETH_TYPE_ARP, dst='00:00:00:00:00:00', src='00:00:00:00:00:00'))		
		ofproto = datapath.ofproto
		parser = datapath.ofproto_parser		
		pkt.serialize()
		data = pkt.data
		actions = [parser.OFPActionOutput (port=ofproto.OFPP_ALL)]
		out = parser.OFPPacketOut(datapath=datapath, 
									buffer_id=ofproto.OFP_NO_BUFFER,
									in_port=in_port, 
									actions=actions,
									data=data)
		datapath.send_msg(out)