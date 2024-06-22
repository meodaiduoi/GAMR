import networkx as nx

from extras.sys_util import mac_to_int
from extras.datatype import NetworkStat
from extras.network_unit_utils import get_link_to_port

from routingapp.common.routing_utils import *
from routingapp.common.models import MultiRouteTasks
from routingapp.compare_algorithm.dijkstra.dijkstra_cost_normalise import Graph, routing_k

from routingapp.dependencies import *
from extras.datatype import NetworkStat
from extras.network_unit_utils import get_link_to_port

def dijkstra_solver(tasks: MultiRouteTasks, network_stat: NetworkStat):
    '''
        Routing using QoS Dijkstra
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
    # print(nx.node_link_data(graph))
    
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

    # !NOTE: Move code section above into new func
     
    # Reading request
    routes = tasks.route
    requests = []
    
    mapping = dict(zip(graph.nodes(), range(1, len(graph.nodes())+1)))
    print(mapping)
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
    graph_gen.updateGraph(update_delay, update_link_utilization, update_loss)
    result = routing_k(graph_gen,requests, 1)

    # return flowrule based on json result format
    result_list = []
    # print(result.chromosome)
    # print(mapping)
    for requests in result:
        print("Request", requests)
        src = get_key(mapping,requests[0])
        dst = get_key(mapping,requests[1])
        src = int(src[1:])
        dst = int(dst[1:])
        request_result_map = []
        for i in requests[2][1:-1]:
            request_result_map.append(int(get_key(mapping, i)))
        # print("Hello")
        route = {
            'src_host': src,
            'dst_host': dst,
            'path_dpid': request_result_map
        }
        result_list.append(route)
    result_json = {
        'route': result_list
    }
    print(f"result: {result}")
    flowrules = create_flowrule_json(result_json, host_json, get_link_to_port())
    return flowrules