import networkx as nx
from routingapp.compare_algorithm.sec_morl_multipolicy.train import train_sdn_policy
from routingapp.common.routing_utils import * 
from routingapp.common.models import MultiRouteTasks
from routingapp.compare_algorithm.sec_morl_multipolicy.module_function import Function
from routingapp.compare_algorithm.sec_morl_multipolicy.module_graph import Graph
import networkx as nx

from routingapp.dependencies import *
from routingapp.common.datatype import NetworkStat

def preprocessing(graph):
    G = nx.Graph()
    for i in range(len(graph)):
        G.add_node(i)
    for i in range(len(graph)):
        for j in graph[i]:
            G.add_edge(i, j)
    # pos = nx.spring_layout(G) #
    # nx.draw(G, pos, with_labels=True)
    # plt.show()
    return G

def result_to_json(result, mapping):
    result_list = []
    print(result)
    # print(mapping)
    for request in result:
        for req in request:
            print("Result", req)
            src = get_key(mapping,req[0])
            dst = get_key(mapping,req[-1])
            request_result_map = []
            for i in req[1:-1]:
                print("I", i)
                request_result_map.append(int(get_key(mapping, i)))
            # src = int(src[1:])
            # dst = int(dst[1:])
            # request_result_map = []
            # for i in request[2][1:-1]:
            #     request_result_map.append(int(get_key(mapping, i)))
            # print("Hello")
            
            # This is output format for solved solution
            route = {
                'src_host': src,
                'dst_host': dst,
                'path_dpid': request_result_map
            }
            
            result_list.append(route)
    result_json = {
        'route': result_list
    }
    print(result_json['route'])
    return result_json 

# # DFS function to find paths from source to destination
# def dfs(graph, start, goal):
#     visited = set()  # List of visited nodes
#     stack = [(start, [start])]  # Stack containing pairs (node, path from source to node)

#     while stack:
#         node, path = stack.pop()  # Get the last node from the stack and the path to it
#         if node not in visited:
#             visited.add(node)
#             if node == goal:
#                 return path  # Return the path from source to destination
#             neighbors = graph.adj_matrix[node]  # Access neighbors from the adjacency matrix of the graph
#             for neighbor in reversed(neighbors):  # Traverse neighbors in reverse order to use stack
#                 if neighbor not in visited:
#                     stack.append((neighbor, path + [neighbor]))  # Add unvisited neighbors to stack with path to that node

#     return None  # If no path from source to destination is found




def sec_solver(tasks: MultiRouteTasks, network_stat: NetworkStat):

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
    update_bandwidth = []
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
            link_utilization = stat.get('link_utilization', 0)
            if link_utilization is None: link_utilization = 0
            update_delay.append((src, dst, delay))
            update_loss.append((src, dst, loss))
            update_bandwidth.append((src, dst, bandwidth))
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
    print("Requests", requests)
    # Solving problem to find solution
    number_node = len(adj_matrix)-1
    clients = []
    edge_servers = []
    cloud_servers = []
    edges = []
    # Generate edges from adjacency matrix
    for i in range(1, number_node+1):
        for j in adj_matrix[i]:
            edges.append([i, j])
    # Generate the list of clients, edge servers, and cloud servers by randomly selecting nodes
    for i in range(1, number_node+1):
        # Choose one cloud server
        if i == 1:
            cloud_servers.append(i)
        # Choose one edge server
        elif i == 2 or i == 3 or i == 4:
            edge_servers.append(i)
        # Choose the rest as clients
        else:
            clients.append(i)
        
    # Generate the promising paths using DFS 
    nx_graph_gen = preprocessing(adj_matrix)
    promising_paths = []
    for src, dst in requests:
        predecessors = list(nx.dfs_edges(nx_graph_gen, source=src))  # Use BFS to find predecessors
        promising_paths.append(predecessors)
    # Create new adjacency graph based on the promising paths
    # 1. Identify nodes involved in any DFS path:
    all_dfs_nodes = set()  # Store all nodes encountered during DFS
    for node in promising_paths:
        for src, dst in node: 
            if src not in all_dfs_nodes:
                all_dfs_nodes.add(src)
            if dst not in all_dfs_nodes:
                all_dfs_nodes.add(dst) 
    # Update the edge servers, cloud servers, and client nodes accordingly
    new_clients = [node for node in clients if node in all_dfs_nodes]   
    new_edge_servers = [node for node in edge_servers if node in all_dfs_nodes]
    new_cloud_servers = [node for node in cloud_servers if node in all_dfs_nodes]

    new_adj_matrix = [[] for _ in range(len(all_dfs_nodes)+1)]
    for edge in edges:
        for node in promising_paths:
            for src, dst in node: 
                if (edge[0] == src and edge[1] == dst) or edge[0] in new_edge_servers or edge[1] in new_edge_servers or edge[0] in new_cloud_servers or edge[1] in new_cloud_servers:
                    if edge[1] not in new_adj_matrix[edge[0]]:
                        new_adj_matrix[edge[0]].append(edge[1])
                    if edge[0] not in new_adj_matrix[edge[1]]:
                        new_adj_matrix[edge[1]].append(edge[0])
            for src, dst in requests:
                    if edge[0] == src or edge[1] == dst:
                        if edge[1] not in new_adj_matrix[edge[0]]:
                            new_adj_matrix[edge[0]].append(edge[1])
                        if edge[0] not in new_adj_matrix[edge[1]]:
                            new_adj_matrix[edge[1]].append(edge[0])
    # Define the graph object
    graph_gen = Graph(len(all_dfs_nodes), len(new_clients), len(new_edge_servers), len(new_cloud_servers), len(new_clients), new_clients, new_edge_servers, new_cloud_servers, new_adj_matrix)

    func = Function()
    graph_gen.updateGraph(update_delay, update_loss, update_bandwidth, update_link_utilization) 
    
    # Use the trained models to generate solutions
    solutions = func.generate_solutions(graph_gen, requests)  
    
    # result = func.select_solution(solutions)

    # Return flow rules based on JSON result format
    result_json = result_to_json(solutions, mapping)
    flowrules = create_flowrule_json(result_json, host_json, get_link_to_port())
    return send_flowrule_single(flowrules)
