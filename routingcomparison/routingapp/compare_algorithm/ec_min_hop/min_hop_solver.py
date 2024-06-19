import networkx as nx
from routingapp.common.models import MultiRouteTasks
from routingapp.compare_algorithm.sec_morl_multipolicy.module_graph import Graph
import networkx as nx
import random

from routingapp.dependencies import *
from extras.datatype import NetworkStat
from extras.sys_util import mac_to_int
from extras.network_unit_utils import get_host, get_link_to_port

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
def select_source_server(graph, src_node):
  """
  Selects a random edge or cloud server as the source for pushing traffic.

  Args:
      graph: An object representing the network graph.
      src_node: The original source node from the request.

  Returns:
      The chosen edge or cloud server node ID.
  """
  # Identify edge and cloud server nodes
  edge_servers = graph.edge_servers
  cloud_servers = graph.cloud_servers

  # Choose a random server type (edge or cloud)
  server_type = random.choice(['edge', 'cloud'])

  # Select a random server node of the chosen type
  if server_type == 'edge':
    chosen_server = random.choice(edge_servers)
  else:
    chosen_server = random.choice(cloud_servers)

  # Ensure the chosen server is not the original source node
  while chosen_server == src_node:
    if server_type == 'edge':
      chosen_server = random.choice(edge_servers)
    else:
      chosen_server = random.choice(cloud_servers)

  return chosen_server

def min_hop_routing(graph, nx_graph, request):
  """
  Implements min-hop routing algorithm using NetworkX.

  Args:
      graph: An object representing the network graph (assumed to be a NetworkX graph).
      request: A list of source-destination pairs.

  Returns:
      A list of solutions (paths) for each request.
  """
  solutions = []
  for src, dst in request:
    try:
        chosen_server = select_source_server(graph, src)
        routing_path = nx.shortest_path(nx_graph, source = src, target = chosen_server) 
        destination_path = nx.shortest_path(nx_graph, source = chosen_server, target = dst)  
        complete_path = routing_path + destination_path[1:]
        solutions.append(complete_path)
    except nx.NetworkXNoPath:
        solutions.append([])  # Handle cases where no path exists
  return solutions
def result_to_json(result, mapping):
    result_list = []
    # print(result)
    # print(mapping)
    for request in result:
        # print("Result", request)
        src = get_key(mapping,request[0])
        dst = get_key(mapping,request[-1])
        request_result_map = []
        for i in request[1:-1]:
            request_result_map.append(int(get_key(mapping, i)))
        src = int(src[1:])
        dst = int(dst[1:])
        route = {
            'src_host': src,
            'dst_host': dst,
            'path_dpid': request_result_map
        }
            
        result_list.append(route)
    result_json = {
        'route': result_list
    }
    # print(result_json['route'])
    return result_json 



def min_hop_solver(tasks: MultiRouteTasks, network_stat: NetworkStat):

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
    # Define the graph object
    graph_gen = Graph(number_node, len(clients), len(edge_servers), len(cloud_servers), len(clients), clients, edge_servers, cloud_servers, adj_matrix)

    graph_gen.updateGraph(update_delay, update_loss, update_bandwidth, update_link_utilization) 
    
    solutions = min_hop_routing(graph_gen, nx_graph_gen, requests)
    

    # Return flow rules based on JSON result format
    result_json = result_to_json(solutions, mapping)
    flowrules = create_flowrule_json(result_json, get_host(), get_link_to_port())
    return flowrules