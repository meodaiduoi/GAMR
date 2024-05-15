import numpy as np
import networkx as nx
import json

from routingapp.compare_algorithm.gamr.module_graph import Graph

from routingapp.common.routing_utils import *
from routingapp.common.models import *
from extras.utils import *

def normalize_weight(graph, priority):
    if priority == 1:
        a = 1/2
        b = 1/2
    elif priority == 2:
        a = 0.3
        b = 0.7
    else:
        a = 0.6
        b = 0.4
    
    graph_cost = np.zeros((graph.number_nodes+1, graph.number_nodes+1))
    max_delay = max(graph.predict_delay.flatten())
    max_bandwidth = max(graph.predict_bandwidth.flatten())
    if max_delay == 0:
        max_delay = 1
    if max_bandwidth == 0:
        max_bandwidth = 1
    for i in range(graph.number_nodes+1):
        for j in range(graph.number_nodes+1):
            graph_cost[i][j] = a * graph.predict_bandwidth[i][j] / max_bandwidth + b * graph.predict_delay[i][j] / max_delay
    return graph_cost


def dijkstra(graph, priority, source, destination):
    # print("Nguon", source)
    # print("Dich", destination)
    # print("Hello dong")
    graph_cost = normalize_weight(graph, priority)
    dist = np.zeros(graph.number_nodes+1)
    prev = np.zeros(graph.number_nodes+1)
    Q = []
    for i in range(1,graph.number_nodes+1):
        dist[i] = float('inf')
        prev[i] = -1
        Q.append(i)
    dist[source] = 0
    while len(Q) != 0:
        min_dist = float('inf')
        u = -1
        for i in Q:
            if dist[i] < min_dist:
                min_dist = dist[i]
                u = i
        # print("Hello")
        # print(Q)
        if u < 0: break 
        else: 
            Q.remove(u)
        # for v in range(1, graph.number_nodes+1):
        #     if graph_cost[u][v] != 0:
        #         alt = dist[u] + graph_cost[u][v]
        #         if alt < dist[v]:
        #             dist[v] = alt
        #             prev[v] = u
        for v in graph.adj_matrix[u]:
            alt = dist[u] + graph_cost[u][v]
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
    path = []
    u = destination
    while prev[u] != -1:
        path.append(int(u))
        u = int(prev[u])
    path.append(source)
    path.reverse()
    print(path)
    return path   

def routing_k(graph, pair_list, priority):
    path_list = []
    for pair in pair_list:
        path = dijkstra(graph, priority, pair[0], pair[1])
        path_list.append((pair[0],pair[1],path))
    return path_list