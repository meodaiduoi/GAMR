from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import uvicorn

import requests as rq 
import networkx as nx

from ga.module_function import Function
from ga.module_evole import Evolutionary
from ga.module_memset import MemSet
from ga.module_population import Population
from ga.module_graph import Graph

app = FastAPI()
memset = MemSet()

@app.get('/')
async def hello():
    return {'hello': 'world'}

class SrcDst(BaseModel):
    src_host: int
    dst_host: int

class RouteTask(BaseModel):
    route: list[SrcDst]

def get_topo():
    topo_json = rq.get('http://0.0.0.0:8080/topology_graph').json()
    return topo_json, nx.json_graph.node_link_graph(topo_json)

def get_host():
    return rq.get('http://0.0.0.0:8080/hosts').json()

def get_key(dict, value):
    for key, val in dict.items():
        if val == value:
           return key
        
def print_json(result, mapping):
    resul_list = []
    for request in result.chromosome:
        src = get_key(mapping,request[0])
        dst = get_key(mapping,request[1])
        src = int(src[1:])
        dst = int(dst[1:])
        path = {
            'src_host': src,
            'dst_host': dst,
            'path_dpid': request[2][1:-1]

        }
        resul_list.append(path)
    result_json = {
        "path": resul_list
    }
    return result_json  

@app.post('/routing')
def routing(task: RouteTask):
    '''
        abc.
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

    return print_json(result, mapping)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8003)



