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
import networkx as nx
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
        
        @self.post('address')
        async def address(name: str):
            device = net.getNodeByName(name)
            return {
                'mac': device.MAC(),
                'ip': device.IP()
            }
        
        @self.get('graph')
        async def get_graph():
            # Create an empty NetworkX graph
            graph = nx.DiGraph()

            # Add nodes to the graph
            for node in net.nodes:
                graph.add_node(node.name)

            # Add edges to the graph
            for link in net.links:
                src = link.intf1.node.name
                dst = link.intf2.node.name
                graph.add_edge(src, dst)
                graph.add_edge(dst, src)
                
            # Serialize the JSON object
            graph_json = nx.node_link_data(graph)
            return graph_json
        
        @self.post('set_link')
        def set_link(set_link: SetLink):
            '''
                turn on/off a link between 2 nodes
            '''    
            node1: Node = net.get(link.name_node1)
            node2: Node = net.get(link.name_node2)
            link: Link = node1.linkTo(node2)
            if set_link.turn_on == False:
                link.intf1.link_down()
                return {'status': 'down'}
            if set_link.turn_on == True:
                link.intf1.link_up()
                return {'status': 'up'}
