from fastapi import FastAPI
import uvicorn

import networkx as nx
import requests as rq

from ga.module_function import Function
from ga.module_evole import Evolutionary
from ga.module_memset import MemSet
from ga.module_population import Population
from ga.module_graph import Graph

from helper.utils import *
from helper.models import *

import sys
sys.stdout.write("\x1b]2;Rest_dynamicsdn\x07")

import argparse

argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="dynamicsdn startup rest api port")
argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port")
args = argParser.parse_args()

DYNAMICSDN_PORT = args.rest_port
RYU_PORT = args.ryu_port

app = FastAPI()
memset = MemSet()

@app.get('/')
async def hello():
    return {'hello': 'world'}


@app.post('/routing')
async def routing(task: RouteTask):
    '''
        Routing using GA alogrithm
    '''
    topo_json, graph = get_topo()
    host_json = get_host()
    link_qualitys = rq.get('http://0.0.0.0:8080/link_quality').json()

    # Add host to graph
    for host in host_json['hosts']:
        dpid_int = mac_to_int(host['port']['dpid'])
        host_int = mac_to_int(host['mac'])
        print(f'dpid_int: {dpid_int}, host_int: {host_int}')
        
        # Add node to graph
        graph.add_node(f'h{host_int}', type='host')
        # add bi-directional link between host and switch
        graph.add_edge(f'h{host_int}', dpid_int, type='host')
        graph.add_edge(dpid_int, f'h{host_int}', type='host')

    # print graph to json
    print(nx.node_link_data(graph))
    
    # Mapping host h{int} to int
    mapping = dict(zip(graph.nodes(), range(1, len(graph.nodes())+1)))
    print(mapping)
    # Creating adj-matrix of graph
    number_node = len(graph.nodes())
    bin_matrix = nx.adjacency_matrix(graph).todense()
    adj_matrix = [[] for i in range(number_node+1)]
    for i in range(1, number_node+1):
        for j in range(1, number_node+1):
            if bin_matrix[i-1][j-1] == 1:
                adj_matrix[i].append(j)

    # Update Links QoS parameters from /topology_graph
    topo_json['links']
    update_delay = []
    update_bandwidth = []
    update_loss = []
    for link in topo_json["links"]:
        #print(link)
        src = mapping[link["source"]]
        dst = mapping[link["target"]]
        if src != dst:
            delay = link.get("delay", 0)
            if delay == None: delay = 0
            loss = link.get("packet_loss", 0)
            if loss == None: loss = 0
            bandwidth = link.get("free_bandwidth", 0)
            if bandwidth == None: bandwidth = 0
            update_delay.append((src, dst, delay))
            update_loss.append((src, dst, loss))
            update_bandwidth.append((src, dst, bandwidth))
    
    # Get from data from /link_quality
    # update_delay = []
    # update_bandwidth = []
    # update_loss = []
    # for qos in link_qualitys:
    #     src = mapping[qos['src.dpid']]
    #     dst = mapping[qos['dst.dpid']]
    #     if src != dst:
    #         delay = qos.get('delay', 0)
    #         if delay == None: delay = 0
    #         loss = qos.get('packet_loss', 0)
    #         if loss == None: loss = 0
    #         bandwidth = qos.get('free_bandwidth', 0)
    #         if bandwidth == None: bandwidth = 0
    #         update_delay.append((src, dst, delay))
    #         update_loss.append((src, dst, loss))
    #         update_bandwidth.append((src, dst, bandwidth))
     
    # Reading request
    routes = task.route
    request = []
    for route in routes:
        # src = 'h' + str(router['src_host'])
        src = f'''h{route.src_host}'''
        dst = f'''h{route.dst_host}'''
        src = mapping[src]
        dst = mapping[dst]
        request.append((src, dst))

    # Sovling problem to find solution
    number_node = len(adj_matrix)-1
    clients = []
    servers = []
    graph_gen = Graph(number_node, 10, 10, 10, clients, servers, adj_matrix)
    print("Danh sach ke:", graph_gen.adj_matrix)
    for band in graph_gen.predict_bandwidth:
        band = 9999
    func = Function()

    graph_gen.updateGraph(update_delay, update_loss, update_bandwidth) 
    pop = Population()
    pop.generate_population(graph_gen, func, 50, len(request), request, memset)

    evol = Evolutionary()
    solutions = evol.evolve1(pop, func, graph_gen, 50, 50, 0.1, 10)
    result = func.select_solution(solutions)

    memset.addAllPath(solutions, request)

    # return flowrule based on json result format
    result = result_to_json(result, mapping)
    print(f"result: {result}")
    flowrules = create_flowrule_json(result, host_json, get_link_to_port())
    send_flowrule(flowrules, RYU_PORT)
    return flowrules
    
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=DYNAMICSDN_PORT)



