import asyncio
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import mininet
from mininet.net import Mininet, Host
from subprocess import Popen

from mn_restapi.mn_restapi_model import *

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