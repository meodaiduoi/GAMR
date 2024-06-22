import networkx as nx

from extras.sys_util import mac_to_int
from extras.datatype import NetworkStat
from extras.network_unit_utils import get_link_to_port

from routingapp.common.routing_utils import *
from routingapp.common.models import MultiRouteTasks

from routingapp.compare_algorithm.moea_d.function_moead import Function
from routingapp.compare_algorithm.moea_d.evole_moead import Evolutionary
from routingapp.compare_algorithm.moea_d.population_moead import Population
from routingapp.compare_algorithm.moea_d.graph_moead import Graph

def moead_solver(tasks: MultiRouteTasks, network_stat: NetworkStat):
    '''
        Routing using GA alogrithm
    '''
    
    graph = network_stat.graph
    host_json = network_stat.host_json
    link_info = network_stat.link_info
    
    # Add host to graph
    for host in host_json['hosts']:
        dpid_int = mac_to_int(host['port']['dpid'])
        host_int = mac_to_int(host['mac'])
        # print(f'dpid_int: {dpid_int}, host_int: {host_int}')
        
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
   
    # Get from data from /link_quality
    update_delay = []
    update_link_utilization = []
    update_loss = []
    for stat in link_info:
        src = mapping[stat['src.dpid']]
        dst = mapping[stat['dst.dpid']]
        if src != dst:
            delay = stat.get('delay', 0)
            if delay == None: delay = 0
            loss = stat.get('packet_loss', 0)
            if loss == None: loss = 0
            bandwidth = stat.get('link_utilization', 0)
            if bandwidth == None: bandwidth = 0
            update_delay.append((src, dst, delay))
            update_loss.append((src, dst, loss))
            update_link_utilization.append((src, dst, bandwidth))
     
    # Reading request
    routes = tasks.route
    requests = []
    
    for route in routes:
        src = f'h{route.src_host}'
        dst = f'h{route.dst_host}'
        src = mapping[src]
        dst = mapping[dst]
        print('reading rq', src, dst)
        requests.append((src, dst))

    # Sovling problem to find solution
    number_node = len(adj_matrix)-1
    clients = []
    servers = []
    graph_gen = Graph(number_node, 10, 10, 10, clients, servers, adj_matrix)
    print("Danh sach ke:", graph_gen.adj_matrix)

    func = Function()

    graph_gen.updateGraph(update_delay, update_loss, update_link_utilization) 
    pop = Population(3,50)
    pop.generate_population(graph_gen, func, 50, len(requests), requests)

    evol = Evolutionary()
    solutions = evol.evolve1(pop, func, graph_gen, 50, 50, 0.1, 10)
    result = func.select_solution(solutions)

    # return flowrule based on json result format
    result = result_to_json(result, mapping)
    print(f"result: {result}")
    flowrules = create_flowrule_json(result, host_json, get_link_to_port())
    return send_flowrule_single(flowrules)
