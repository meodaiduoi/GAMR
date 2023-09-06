import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import mininet
from mininet.net import Mininet, Host, Node, Link
from subprocess import Popen

from mn_restapi.mn_restapi_model import *
from mn_restapi.util import *
# from mn_restapi.spanning_tree import SpanningTree, convert_network

import networkx as nx
import logging
import re

class RestHookMN(FastAPI):
    def __init__(self, net: Mininet):
        super().__init__(title='fastapi hook for mininet',
                         description='')
        self.net = net

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
            
            src_host = net.getNodeByName(src_host)
            dst_host = net.getNodeByName(dst_host)
            
            output = src_host.popen(
                f'ping {dst_host.IP} -c {task.count} -W {task.timeout}',
                shell=True).communicate()[0].decode('latin-1')
            
            # Extract packet loss percentage
            packet_loss = re.search(r"(\d+)% packet loss", output).group(1)
            # print("Packet Loss Percentage:", packet_loss)
            
            # Extract average RTT
            avg_rtt = re.search(r"avg\/max\/mdev = (\d+\.\d+)", output).group(1)
            # print("Average RTT:", avg_rtt, "ms")
            
            return {
                'packet_loss': packet_loss,
                'delay': avg_rtt
            }

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

        @self.post('/address')
        async def address(name: str):
            '''
                Get MAC and IP address of a given hostname/switch/nod
            '''
            device = net.getNodeByName(name)
            return {
                'mac': device.MAC(),
                'ip': device.IP()
            }

        @self.get('/graph')
        async def get_graph():
            '''
                Return Mininet network graph
            '''
            graph = convert_network(self.net)
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

        # @self.get('/link_probing')
        # def link_probing():
        #     '''
        #         Using spanning tree algrothim to cut off loop on the network
        #         then pingall
        #     '''
        #     graph = convert_network(self.net)
        #     stree = SpanningTree(graph)

        #     for link in stree.solution_invert()[0]:
        #         print(link)
        #         self.net.configLinkStatus(link[0], link[1], 'down')

        #     net.pingAll('1')

        #     for link in stree.solution_invert()[0]:
        #         print(link)
        #         self.net.configLinkStatus(link[0], link[1], 'up')

        #     # return stree value as json
        #     return { stree.solution_as_networkx() }

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

