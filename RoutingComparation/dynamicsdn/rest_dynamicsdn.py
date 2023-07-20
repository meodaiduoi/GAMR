from fastapi import FastAPI
import uvicorn

import networkx as nx

from ga.module_function import Function
from ga.module_evole import Evolutionary
from ga.module_memset import MemSet
from ga.module_population import Population
from ga.module_graph import Graph

from helper.utils import *
from helper.models import *

import argparse

argParser = argparse.ArgumentParser()
argParser.add_argument("rest_port", type=int, help="dynamicsdn startup rest api port")
argParser.add_argument("ryu_port", type=int, help="remote ryu rest api port")
args = argParser.parse_args()

DYNAMICSDN_PORT = args.rest_port
RYU_PORT = args.ryu_port

# import tomllib
# try:
#     with open("config.toml", "rb") as f:
#         toml_dict = tomllib.load(f)
# except tomllib.TOMLDecodeError:
#     print("Yep, definitely not valid.")

# RESTHOOKMN_PORT = toml_dict['service-port']['resthookmn']
# DYNAMICSDN_PORT = toml_dict['service-port']['dynamicsdn']
# SIMPLEHTTPSERVER_PORT = toml_dict['service-port']['simplehttpserver']




app = FastAPI()
memset = MemSet()

@app.get('/')
async def hello():
    return {'hello': 'world'}


@app.post('/routing')
def routing(task: RouteTask):
    '''
        
    '''
    topo_json, graph = get_topo()
    host_json = get_host()

    # Add host to graph
    for host in host_json['hosts']:
        host_id = int(host['mac'].translate(str.maketrans('','',":.- ")), 16)
        graph.add_node(f'h{host_id}', type='host')
        # add bi-directional link between host and switch
        graph.add_edge(f'h{host_id}', int(host['port']['dpid']), type='host')
        graph.add_edge(int(host['port']['dpid']), f'h{host_id}', type='host')

    # Mapping host h{int} to int
    mapping = dict(zip(graph.nodes(), range(1, len(graph.nodes())+1)))
    # Creating adj-matrix of graph
    number_node = len(graph.nodes())
    bin_matrix = nx.adjacency_matrix(graph).todense()
    print(type(bin_matrix))
    adj_matrix = [[] for i in range(number_node+1)]
    for i in range(1, number_node+1):
        for j in range(1, number_node+1):
            if bin_matrix[i-1][j-1] == 1:
                adj_matrix[i].append(j)

    # Update Links QoS parameters
    topo_json['links']
    update_delay = []
    update_bandwidth = []
    update_loss = []
    for link in topo_json["links"]:
        #print(link)
        src = mapping[link["source"]]
        dst = mapping[link["target"]]
        if src != dst:
            delay = link["delay"]
            loss = link["packet_loss"]
            bandwidth = link["free_bandwith"]
            update_delay.append((src, dst, delay))
            update_loss.append((src, dst, loss))
            update_bandwidth.append((src, dst, bandwidth))
     
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
    return create_flowrule_json(result, host_json, get_link_to_port())

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=DYNAMICSDN_PORT)



