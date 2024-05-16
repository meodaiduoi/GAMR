import networkx as nx
from routingapp.compare_algorithm.sec_morl_multipolicy.train import train_sdn_policy
from routingapp.common.routing_utils import * 
from routingapp.common.models import RouteTask
from routingapp.compare_algorithm.sec_morl_multipolicy.module_function import Function
from routingapp.compare_algorithm.sec_morl_multipolicy.module_graph import Graph

from routingapp.dependencies import *
from routingapp.common.datatype import NetworkStat

def result_to_json(result, mapping):
    result_list = []
    # print(result)
    # print(mapping)
    for request in result:
        print("Request", request)
        src = get_key(mapping,request[0])
        dst = get_key(mapping,request[1])
        src = int(src[1:])
        dst = int(dst[1:])
        request_result_map = []
        for i in request[2][1:-1]:
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
    print(result_list)
    return result_json 

# DFS function to find paths from source to destination
def dfs(graph, start, goal):
    visited = set()  # List of visited nodes
    stack = [(start, [start])]  # Stack containing pairs (node, path from source to node)

    while stack:
        node, path = stack.pop()  # Get the last node from the stack and the path to it
        if node not in visited:
            visited.add(node)
            if node == goal:
                return path  # Return the path from source to destination
            neighbors = graph.adj_matrix[node]  # Access neighbors from the adjacency matrix of the graph
            for neighbor in reversed(neighbors):  # Traverse neighbors in reverse order to use stack
                if neighbor not in visited:
                    stack.append((neighbor, path + [neighbor]))  # Add unvisited neighbors to stack with path to that node

    return None  # If no path from source to destination is found


# def generate_k_best_graph(graph_gen, request, k):
#     """
#     Generate the graph for the K best paths from source to destination.
#     """
#     k_best_paths = []
#     for src, dst in request:
#         # Perform DFS to find K best paths from src to dst
#         paths = dfs(graph_gen, src, dst, k)
#         k_best_paths.extend(paths)
    
#     # Combine all paths into a single set of nodes
#     all_nodes = set()
#     for path in k_best_paths:
#         all_nodes.update(path)

#     # Generate a subgraph containing all nodes in the combined paths
#     combined_graph = graph_gen.subgraph(list(all_nodes))
    
#     return combined_graph

def sec_solver(task: RouteTask, network_stat: NetworkStat):

    graph = network_stat.graph
    host_json = network_stat.host_json
    link_info = network_stat.link_info

    # Add host to graph
    for host in host_json['hosts']:
        dpid_int = mac_to_int(host['port']['dpid'])
        host_int = mac_to_int(host['mac'])
        
        # Add node to graph with the determined type
        graph.add_node(f'h{host_int}', type='host')
        # add bi-directional link between host and switch
        graph.add_edge(f'h{host_int}', dpid_int, type='host')
        graph.add_edge(dpid_int, f'h{host_int}', type='host')

    # Mapping host h{int} to int
    mapping = dict(zip(graph.nodes(), range(1, len(graph.nodes())+1)))
    print(mapping)
    
    # Creating adj-matrix of graph
    number_node = len(graph.nodes())
    bin_matrix = nx.adjacency_matrix(graph).todense()
    adj_matrix = [[] for _ in range(number_node+1)]
    for i in range(1, number_node+1):
        for j in range(1, number_node+1):
            if bin_matrix[i-1][j-1] == 1:
                adj_matrix[i].append(j)

    # Get data from /link_quality
    update_delay = []
    update_link_utilization = []
    update_loss = []
    for stat in link_info:
        src = mapping[stat['src.dpid']]
        dst = mapping[stat['dst.dpid']]
        if src != dst:
            delay = stat.get('delay', 0)
            if delay is None: delay = 0
            loss = stat.get('packet_loss', 0)
            if loss is None: loss = 0
            bandwidth = stat.get('link_utilization', 0)
            if bandwidth is None: bandwidth = 0
            update_delay.append((src, dst, delay))
            update_loss.append((src, dst, loss))
            update_link_utilization.append((src, dst, bandwidth))
     
    # Reading request
    # !NOTE CHANGE TO SINGLE ROUTE TASK REWORK THIS SECTION
    route = task.route
    request = []
    src = f'h{route.src_host}'
    dst = f'h{route.dst_host}'
    src = mapping[src]
    dst = mapping[dst]
    print('reading rq', src, dst)
    request.append((src, dst))

    # Solving problem to find solution
    number_node = len(adj_matrix)-1
    clients = []
    edge_servers = []
    cloud_servers = []
    graph_gen = Graph(number_node, 10, 10, 10, 10, clients, edge_servers, cloud_servers, adj_matrix)

    func = Function()
    graph_gen.updateGraph(update_delay, update_loss, update_link_utilization) 
    
    # Generate the promising paths using DFS 
    promising_paths = []
    for src, dst in request:
        path = dfs(graph, src, dst)
        if path:
            promising_paths.append(path)

    # Create a subgraph containing all nodes in the promising paths
    promising_nodes = set()
    for path in promising_paths:
        promising_nodes.update(path)
    promising_graph = graph.subgraph(list(promising_nodes))

    print(promising_graph.adj_matrix, promising_graph.number_nodes, promising_graph.number_edge_servers, promising_graph.number_clients, promising_graph.number_cloud_servers)
    for req in request: 
        # print(req)
        # DRL to decide the best path for multi-objective reward
        trained_models = train_sdn_policy(promising_graph, func, req)
        
    # Use the trained models to generate solutions
    solutions = func.generate_solutions(promising_graph, func, request)  
    
    result = func.select_solution(solutions)

    # Return flow rules based on JSON result format
    result_json = result_to_json(result, mapping)
    print(f"result: {result}")
    flowrules = create_flowrule_json(result_json, host_json, get_link_to_port())
    return flowrules
