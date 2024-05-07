import numpy as np

class Graph:
    def __init__(self, number_nodes, number_clients, number_edge_servers, number_cloud_servers, clients, edge_servers, cloud_servers, adj_matrix):
        self.number_nodes = number_nodes
        self.number_clients = number_clients
        self.number_edge_servers = number_edge_servers
        self.number_cloud_servers = number_cloud_servers
        self.clients = clients
        self.edge_servers = edge_servers
        self.cloud_servers = cloud_servers
        self.adj_matrix = adj_matrix
        self.predict_delay = np.zeros((self.number_nodes+1, self.number_nodes+1))
        self.predict_loss = np.zeros((self.number_nodes+1, self.number_nodes+1))
        self.predict_bandwidth = np.zeros((self.number_nodes+1, self.number_nodes+1))

    # delay_list includes (first_node, second_node, new_delay) tuple
    # loss_list include (first_node, second_node, new_delay) tuple
    # bandwidth_list include (first_node, second_node, new_bandwidth) tuple
    def updateGraph(self, delay_list, loss_list, bandwidth_list):
        for a in delay_list:
            self.predict_delay[a[0]][a[1]] = a[2]
            # self.predict_delay[a[1]][a[0]] = a[2]
        for a in loss_list:
            self.predict_loss[a[0]][a[1]] = a[2]
            # self.predict_loss[a[1]][a[0]] = a[2]
        for a in bandwidth_list:
            self.predict_bandwidth[a[0]][a[1]] = a[2]
            # self.predict_bandwidth[a[1]][a[0]] = a[2]
    def subgraph(self, nodes):
            """
            Create a subgraph from the original graph based on the specified list of nodes.
            """
            sub_adj_matrix = np.zeros_like(self.adj_matrix)
            for node1 in nodes:
                for node2 in nodes:
                    if self.adj_matrix[node1][node2] == 1:
                        sub_adj_matrix[node1][node2] = 1
            return Graph(len(nodes), self.number_clients, self.number_edge_servers, self.number_cloud_servers, self.clients, self.edge_servers, self.cloud_servers, sub_adj_matrix)

