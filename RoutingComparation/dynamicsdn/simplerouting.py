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
async def routing(tasks: ManualRouteTasks):
    '''
    Manual routing \n
    
    '''
    mapping, graph = get_full_topo_graph()
    
    flowrules = []
    for task in tasks.route:
        path = [task.src_host] + task.path_dpid + [task.dst_host]
        task.model_dump()
        if nx.is_path(graph, task.path_dpid):
            flowrules.append(create_flowrule_json(task.model_dump(), get_host(), get_link_to_port()))
    return send_flowrule(flowrules, ryu_rest_port=RYU_PORT)

@app.post('/routing/shortest_path')
async def routing(tasks: RouteTasks):
    '''
    Shortest path routing \n
    '''
    mapping, graph = get_full_topo_graph()
    
    solutions = {'route': []}
    flowrules = []
    for task in tasks.route:
        if nx.has_path(graph, task.src_host, task.dst_host):
            path = list(nx.shortest_path(graph, f'h{task.src_host}', f'h{task.dst_host}'))
            solutions['route'].append({
                'src_host': task.src_host,
                'dst_host': task.dst_host,
                'path_dpid': path[1:-1],
            })
            flowrules = create_flowrule_json(solutions, get_host(), get_link_to_port())
    return send_flowrule(flowrules, ryu_rest_port=RYU_PORT)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=DYNAMICSDN_PORT)