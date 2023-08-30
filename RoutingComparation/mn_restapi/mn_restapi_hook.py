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
            proc: Popen = host.popen(task.cmd)
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
            host.cmd(task.cmd)

        @self.post('/ping')
        def ping(task: Ping):
            '''
                Ping between a list of given hostsname then return average packetloss percentage on each host
            '''
            hosts = [net.getNodeByName(hostname) for hostname in task.hostname_list]
            result = net.ping(hosts, task.timeout)
            return { 'packetloss': result }

        @self.post('/pingall')
        def pingall(task: Pingall):
            '''
                Pingall then return average packetloss percentage on each host
            '''
            result = self.net.pingAll(timeout=task.timeout)
            return {'packetloss': result}

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
        def link_quality():
            '''
                Get link quality of all link in the network
            '''
            try:
                return net.topo.link_quality
            except NameError:
                logging.error('Topo object not implemented')
                return 
        
        @self.post('/open_xterm')
        def open_xterm():
        # try:
            net.getNodeByName('h1').cmd('xterm &')
        # except:
            # ...                
            