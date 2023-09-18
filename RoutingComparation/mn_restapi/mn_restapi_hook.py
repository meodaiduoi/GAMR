import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import mininet
from mininet.net import Mininet, Host, Node, Link

from mn_restapi.mn_restapi_model import *
from mn_restapi.util import *
# from mn_restapi.spanning_tree import SpanningTree, convert_network

from mn_restapi.routes import info

from subprocess import Popen
import concurrent.futures

from extras.utils import find_key_from_value

import networkx as nx
import logging
import re

class RestHookMN(FastAPI):
    def __init__(self, net, *args, **params):
        self.net = net
        self.link_ping_stat = {}
        self.sw_mapping = self.net.topo.debug_sw_host_mapping
        super(RestHookMN, self).__init__(title='fastapi hook for mininet',
                         description='', *args, **params)

        # self.include_router(info.router)

        # Startup event section
        async def update_link_ping_stat():
            while True:
                graph = topo_to_nx(self.net, include_host=False)
                adj_list = adj_dict(graph)
                adj_no_dup = adj_ls_no_dup_route(adj_list)
                tasks = []
                stats = []
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=40) as pool:
                    for node1, adj_nodes in adj_no_dup.items():
                        for node2 in adj_nodes:
                            tasks.append(
                                pool.submit(
                                    host_popen_ping,
                                    net,
                                    self.sw_mapping[node1],
                                    self.sw_mapping[node2],
                                    count=30,
                                    interval=0.02,
                                    return_hostname=True))
                    for task in concurrent.futures.as_completed(tasks):
                        result = task.result()
                        node1 = find_key_from_value(self.sw_mapping, result['src_host'])
                        node2 = find_key_from_value(self.sw_mapping, result['dst_host'])
                        stats.append({
                            'src.host': mac_to_int(net.get(node1).dpid),
                            'dst.host': mac_to_int(net.get(node2).dpid),
                            'packet_loss': result['packet_loss'],
                            'delay': result['delay'],
                        })
                        stats.append({
                            'src.host': mac_to_int(net.get(node2).dpid),
                            'dst.host': mac_to_int(net.get(node1).dpid),
                            'packet_loss': result['packet_loss'],
                            'delay': result['delay'],
                        })
                
                self.link_ping_stat = stats
                logging.info(f'Update link ping stat')
                logging.debug(self.link_ping_stat)
                await asyncio.sleep(5)  # Update the variable every 5 seconds

        @self.on_event("startup")
        async def startup_event():
            asyncio.create_task(update_link_ping_stat())

        @self.post('/run_popen')
        def run_popen(task: PopenTask):
            '''
                Using poepn to run task with option to returing result
            '''
            host: Host = self.net.getNodeByName(task.hostname)
            command = command_sanitization(task.cmd)
            proc: Popen = host.popen([command], shell=True)
            if task.wait == True:
                result, err = proc.communicate()

            return { 'result': result.decode("latin-1"),
                     'error': err.decode("latin-1")}

        @self.post('/run_cmd')
        async def run_cmd(task: CmdTask):
            '''
                Run command with the given hostsname
            '''
            host: Host = self.net.getNodeByName(task.hostname)
            command = command_sanitization(task.cmd)
            host.cmd(command)

        @self.post('/run_xterm')
        async def run_xterm(task: CmdTask):
            '''
                Open command in xterm \n
            '''
            try:
                if task.cmd != '':
                    command = command_sanitization(task.cmd, open_in_term=True)
                    net.getNodeByName(f'{task.hostname}').cmd(
                        f'xterm -e "{command}; bash" &'
                    )
                else:
                    net.getNodeByName(f'{task.hostname}').cmd('xterm &')
                return {'status': 'ok'}
            except KeyError:
                logging.error("Invalid hostname")
                return {'status': 500}

        @self.post('/ping')
        def mn_ping(task: Ping):
            '''
                Ping (mininet func)  between a list of given hostsname
                then return average packetloss percentage
                on hosts
            '''
            hosts = [net.getNodeByName(hostname) for hostname in task.hostname_list]
            result = net.ping(hosts, task.timeout)
            return { 'packetloss': result }

        @self.post('/pingall')
        def mn_pingall(task: Pingall):
            '''
                Pingall (mininet func) then return average
                packetloss percentage on hosts
            '''
            result = self.net.pingAll(timeout=task.timeout)
            return {'packetloss': result}

        @self.post('/ping_single')
        def ping_single(task: PingSingle):
            '''
                Using Popen to run ping conmmand on src host:
                "ping {dst_host_ip} -c {count} -W {timeout}"
            '''
            return host_popen_ping(
                net,
                task.src_hostname, task.dst_hostname,
                count=task.count,
                timeout=task.timeout
            )

        @self.get('/device_name')
        async def device_name():
            '''
                get lists of all hostname and switchname \n
            '''
            host_names = [host.name for host in net.hosts]
            switch_names = [switch.name for switch in net.switches]
            return {
                'hostname': host_names,
                'switchname': switch_names
            }
        
        @self.get('/switch_dpid')
        async def switch_dpid():
            '''
                get lists of all switch dpid \n
            '''
            dpid = {}
            for switch in net.switches:
                dpid[switch.name] = mac_to_int(switch.dpid)
            return dpid
                    
        @self.post('/address')
        async def address(name: str):
            '''
                Get MAC and IP address of a given hostname
            '''
            device: Host | Node = net.getNodeByName(name)
            return {
                'mac': device.MAC(),
                'ip': device.IP()
            }

        @self.get('/graph')
        async def get_graph():
            '''
                Return Mininet network graph
            '''
            graph = topo_to_nx(self.net)
            # Serialize the JSON object
            graph_json = nx.node_link_data(graph)
            return graph_json

        @self.post('config_link_status')
        def set_link(config: ConfigLink):
            '''
                turn on/off a link between 2 nodes
            '''
            net.configLinkStatus(config.name1, config.name2, config.status)
            return {'status': 'ok'}

        @self.get('/link_quality')
        async def link_quality():
            '''
                Get link quality of all link in the network
            '''
            try:
                return net.topo.link_quality
            except NameError:
                logging.error('Topo object not implemented')
                return

        @self.get('/link_ping_stat')
        async def link_ping_stat():
            '''
                return link ping stat
            '''
            return self.link_ping_stat

        @self.get('/adj_list/{no_dup}')
        async def adj_list(no_dup: bool | None = False):
            '''
                Get adjacency list of all nodes \n
                no_dup link param:
                    True: remove duplicate route
                    False: return all route
            '''
            graph = topo_to_nx(self.net, include_host=False)
            adj_list = adj_dict(graph)
            if no_dup == True:
                return adj_ls_no_dup_route(adj_list)
            return adj_list


        @self.get('/debug_switch_mapping')
        async def debug_switch_mapping():
            '''
                Debug switch mapping
            '''
            new_dict = {}
            for switch, host in self.sw_mapping.items():
                # switch_dpid = net.get(switch).dpid
                host_mac = net.get(host).MAC()
                new_dict[switch] = mac_to_int(host_mac)
            return new_dict

        @self.get('/link_to_port')
        async def link_to_port():
            '''
                Bypass sdn api by get
                it directly from mininet
            '''
            ...

