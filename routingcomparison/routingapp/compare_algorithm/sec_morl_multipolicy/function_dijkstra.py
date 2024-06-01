import os
import numpy as np
import networkx as nx
import json

# from routingapp.compare_algorithm.gamr.module_graph import Graph

from routingapp.common.routing_utils import *
from routingapp.common.models import *
from extras.utils import *

import heapq
import numpy as np

def normalize_weight(graph, priority):
    if priority == 1:
        a = 1 / 2
        b = 1 / 2
    elif priority == 2:
        a = 0.3
        b = 0.7
    else:
        a = 0.6
        b = 0.4

    max_delay = np.max(graph.predict_delay)
    max_bandwidth = np.max(graph.predict_bandwidth)
    max_delay = max_delay if max_delay != 0 else 1
    max_bandwidth = max_bandwidth if max_bandwidth != 0 else 1

    graph_cost = np.zeros((graph.number_nodes + 1, graph.number_nodes + 1))
    for i in range(graph.number_nodes + 1):
        for j in range(graph.number_nodes + 1):
            if graph.predict_delay[i][j] >= 0 and graph.predict_bandwidth[i][j] >= 0:
                graph_cost[i][j] = a * graph.predict_bandwidth[i][j] / max_bandwidth + b * graph.predict_delay[i][j] / max_delay
    return graph_cost

def dijkstra(graph, priority, source, destination):
    graph_cost = normalize_weight(graph, priority)
    dist = {i: float('inf') for i in range(0, graph.number_nodes)}
    prev = {i: None for i in range(0, graph.number_nodes)}
    dist[source] = 0

    priority_queue = [(0, source)]
    while priority_queue:
        current_dist, u = heapq.heappop(priority_queue)
        

        for v in range(1, graph.number_nodes + 1):
            if graph_cost[u][v] != 0:
                alt = current_dist + graph_cost[u][v]
                if alt < dist[v]:
                    dist[v] = alt
                    prev[v] = u
                    heapq.heappush(priority_queue, (alt, v))
    
    path = []
    u = destination
    if dist[u] == float('inf'):
        return path  # No path found
    while u is not None:
        if(u != -1):
            path.append(int(u))
            u = prev[u]

    path.append(destination)
    path.append(source)
    path.reverse()

    return path

def routing_k(graph, pair_list, priority):
    path_list = []
    for pair in pair_list:
        path = dijkstra(graph, priority, pair[0], pair[1])
        path_list.append((pair[0], pair[1], path))
    return path_list
