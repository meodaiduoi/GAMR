import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import mininet
from mininet.net import Mininet, Host
from subprocess import Popen

from mn_restapi_model import *

class RestHook(FastAPI):
    def __init__(self, net: Mininet):
        super().__init__(title='fastapi hook for mininet',
                         description='')
        self.net = net

        @self.post('/send_task')
        def send_task(task: Task):
            host: Host = self.net.getNodeByName(task.host_name)
            proc: Popen = host.popen(task.cmd)
            if task.wait == True:
                proc.communicate()

        @self.post('/run_cmd')
        def run_cmd(task: Command):
            host: Host = self.net.getNodeByName('h1')
            ...


        @self.post('/ping')
        def ping(task: Ping):
            hosts = []
            for hostname in task.hostname_list:
                hosts.append(net.getNodeByName(task))
            result = net.ping(hosts)
            return { 'packetloss': result }

        @self.get('/pingall')
        # @self.post('/pingall')
        def pingall():
            result = self.net.pingAll()
            return {'packetloss': result}

        @self.get('/device_name')
        def hostname():
            '''
                get lists of all hostnames
            '''
            nodes = net.nodes
            host_names = []
            switch_names = []
            for node in nodes:
                if isinstance(node, mininet.Host):
                    host_names.append(node.name)
                elif isinstance(node, mininet.Switch):
                    switch_names.append(node.name)
            return { 'hostname':host_names, 'switchname': switch_names }
