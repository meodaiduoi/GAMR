import numpy as np

from routingapp.compare_algorithm.gamr.module_graph import Graph

def normalize_weight(graph, priority):
    if priority == 1:
        a = 1/3
        b = 1/3
        c = 1/3
    elif priority == 2:
        a = 0.12
        b = 0.26
        c = 0.62
    elif priority == 3:
        a = 0.18
        b = 0.4
        c = 0.42
    else:
        a = 0.47
        b = 0.31
        c = 0.22
    
    graph_cost = np.zeros((graph.number_nodes+1, graph.number_nodes+1))
    max_delay = max(graph.predict_delay.flatten())
    max_bandwidth = max(graph.predict_bandwidth.flatten())
    max_loss = max(graph.predict_loss.flatten())
    if max_delay == 0:
        max_delay = 1
    if max_bandwidth == 0:
        max_bandwidth = 1
    if max_loss == 0:
        max_loss = 1
    for i in range(graph.number_nodes+1):
        for j in range(graph.number_nodes+1):
            graph_cost[i][j] = a * graph.predict_bandwidth[i][j] / max_bandwidth + b * graph.predict_loss[i][j] / max_loss + c * graph.predict_delay[i][j] / max_delay
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
        # print(u)
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