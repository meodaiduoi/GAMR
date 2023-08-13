from helper.utils import *
from helper.models import *

from fastapi import FastAPI
import uvicorn

import networkx as nx
import requests as rq

import argparse

argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="dynamicsdn startup rest api port")
argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port")
args = argParser.parse_args()

DYNAMICSDN_PORT = args.rest_port
RYU_PORT = args.ryu_port

app = FastAPI()



@app.get('/')
async def hello():
    return {'hello': 'world'}



@app.post('/routing/manual')
async def routing(tasks: ManualRouteTask):
    '''
    Manual routing \n
    
    '''
    mapping, graph: nx.DiGraph = get_full_topo_graph()
    for task in tasks.route:
        path = [task.src_host] + task.path + [task.dst_host]
        if nx.is_path(graph, path):
            create_flowrule_json(get_host(), get_link_to_port(), )
    
    
@app.post('/routing/shortest_path')
async def routing(tasks: RouteTask):
    '''
    Shortest path routing \n
    '''
    mapping, graph: nx.DiGraph = get_full_topo_graph()
    for task in tasks.route:
        if nx.has_path(graph, task.src_host, task.dst_host):
            path = list(nx.shortest_path(graph, task.src_host, task.dst_host))

    ...