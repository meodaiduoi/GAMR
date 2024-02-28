from routingapp.common.utils import *
from routingapp.common.models import *

import asyncio
from typing import Optional
from fastapi import FastAPI
import uvicorn

import networkx as nx
from networkx.readwrite import json_graph
import requests as rq

import time
import argparse

from routingapp.compare_algorithm.dijkstra.dijkstra_solver import dijkstra_solver
from routingapp.compare_algorithm.gamr.ga_solver import gamr_solver
from routingapp.compare_algorithm.gamr.module_memset import MemSet
# from dynamicsdn.compare_algorithm.MultiBandits ?

import logging
memset = MemSet()

argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="dynamicsdn startup rest api port")
argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port or start port if multi_domain==True")
argParser.add_argument("-md", "--multi_domain", type=bool, default=False, help="if network has more than 1 controller")
args = argParser.parse_args()

DYNAMICSDN_PORT = args.rest_port
RYU_PORT = args.ryu_port
MULTI_DOMAIN= args.multi_domain

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title='Routing Api Network',
    description='Routing Api for networking application',
    summary="..."
)

while True:
    try:
        MAPPING, GRAPH = get_full_topo_graph()
        if MULTI_DOMAIN == True:
            GRAPH = json_graph.node_link_graph(
                rq.get('http://0.0.0.0:8000/graph').json()
            )
        break
    except (rq.ConnectionError, rq.ConnectTimeout):
        logging.error('Wait for server connecting...')
        time.sleep(5)
        continue

async def add_flow_adj():
    while True:
        try:
            adj_no_dup: dict = rq.get('http://0.0.0.0:8000/adj_list/True').json()
            debug_host_mapping = rq.get('http://0.0.0.0:8000/debug_switch_mapping').json()
            switchname_mapping =  rq.get('http://0.0.0.0:8000/switch_dpid').json()
            if MULTI_DOMAIN == True:
                host_mn = rq.get('http://0.0.0.0:8000/host').json()
                sw_ctrler_mapping = rq.get('http://0.0.0.0:8000/sw_ctrler_mapping').json()
                link_info = get_link_info('http://localhost:8000/link_info')
                
            solutions = {'route': []}
            for node1, adj_nodes in adj_no_dup.items():
                for node2 in adj_nodes:
                    logging.info(f'add debug flow from {switchname_mapping[node1]} to {switchname_mapping[node2]}')
                    solution = {
                            'src_host':debug_host_mapping[node1],
                            'dst_host':debug_host_mapping[node2],
                            'path_dpid':[switchname_mapping[node1], 
                                        switchname_mapping[node2]]
                    }
                    solutions['route'].append(solution)
            if MULTI_DOMAIN == False:
                send_flowrule(
                    create_flowrule_json(solutions, get_host(), get_link_to_port()))
            else:
                send_flowrule_multidomain_localhost(
                    create_flowrule_multidomain_json(solutions, 
                                                    host_mn,
                                                    link_info),
                                                    sw_ctrler_mapping, RYU_PORT)
            logging.info('Debug flow added sucessfully')
            await asyncio.sleep(500)
        except (rq.ConnectionError, rq.ConnectTimeout) as e:
            logging.error(f"Connection error retrying...")
            await asyncio.sleep(5)
        except TypeError as e:
            print(e)
            logging.error(f'Controller not ready retrying...')
            await asyncio.sleep(5)
        
@app.on_event("startup")
async def startup_event():
    '''
        Startup event \n
    '''
    asyncio.create_task(add_flow_adj())
    logging.info("Startup event")
    
    
@app.get('/')
async def hello():
    return {'hello': 'world'}

@app.post('/routing/manual')
async def routing_manual(tasks: ManualRouteTasks):
    '''
    Manual routing \n
    '''
    
    flowrules = []
    for task in tasks.route:
        path = [task.src_host] + task.path_dpid + [task.dst_host]
        task.model_dump()
        if nx.is_path(GRAPH, task.path_dpid):
            flowrules.append(create_flowrule_json(task.model_dump(), get_host(), get_link_to_port()))
    return send_flowrule(flowrules, ryu_rest_port=RYU_PORT)

@app.post('/routing/min_hop')
async def routing_min_hop(tasks: RouteTasks):
    '''
    Min-hop routing \n
    '''
    
    solutions = {'route': []}
    flowrules = []
    for task in tasks.route:
        if nx.has_path(GRAPH, f'h{task.src_host}', f'h{task.dst_host}'):
            path = list(nx.shortest_path(GRAPH, f'h{task.src_host}', f'h{task.dst_host}'))
            solutions['route'].append({
                'src_host': task.src_host,
                'dst_host': task.dst_host,
                'path_dpid': path[1:-1],
            })
            flowrules = create_flowrule_json(solutions, get_host(), get_link_to_port())
    return send_flowrule(flowrules, ryu_rest_port=RYU_PORT)

@app.post('/routing/dijkstra')
async def routing_dijkstra(task: RouteTasks):
    '''
        Dijkstra algorithm routing
    '''
    return dijkstra_solver(task)
    
@app.post('/routing/gamr')
async def routing_ga(task: RouteTasks):
    '''
        Ga algorithm routing
    '''
    return gamr_solver(task, memset)

@app.get('/routing/add_flow_all')
async def add_flow_all():
    '''
        Not yet implemented
    '''
    ...

@app.post('/routing/nsga-iii')
async def nsga3():
    '''
        nsga-iii algrithm
    '''
    


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=DYNAMICSDN_PORT)