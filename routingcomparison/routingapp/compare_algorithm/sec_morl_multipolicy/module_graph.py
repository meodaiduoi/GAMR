import numpy as np

class Graph:
    def __init__(self, number_nodes, number_clients, number_edge_servers, number_cloud_servers, number_switch, clients, edge_servers, cloud_servers, adj_matrix):
        self.number_nodes = number_nodes
        self.number_clients = number_clients
        self.number_edge_servers = number_edge_servers
        self.number_cloud_servers = number_cloud_servers
        self.number_switch = number_switch
        self.clients = clients
        self.edge_servers = edge_servers
        self.cloud_servers = cloud_servers
        self.adj_matrix = adj_matrix
        self.predict_delay = np.zeros((self.number_nodes+1, self.number_nodes+1))
        self.predict_loss = np.zeros((self.number_nodes+1, self.number_nodes+1))
        self.predict_bandwidth = np.zeros((self.number_nodes+1, self.number_nodes+1))

    def updateGraph(self, delay_list, loss_list, bandwidth_list):
        for a in delay_list:
            self.predict_delay[a[0]][a[1]] = a[2]
        for a in loss_list:
            self.predict_loss[a[0]][a[1]] = a[2]
        for a in bandwidth_list:
            self.predict_bandwidth[a[0]][a[1]] = a[2]

    def subgraph(self, nodes):
        """
        Create a subgraph from the original graph based on the provided list of nodes.

        Parameters:
            nodes (list): The list of nodes to create the subgraph from.

        Returns:
            Graph: The subgraph containing the specified nodes.
        """
        # Initialize an empty list to hold the adjacency matrix of the subgraph
        sub_adj_matrix = []
        # Initialize an empty dictionary to map nodes to their new indices in the subgraph
        sub_nodes = {}

        # Create a new adjacency matrix for the subgraph
        for node in nodes:
            # Append the corresponding row from the original adjacency matrix to the subgraph adjacency matrix
            sub_adj_matrix.append(self.adj_matrix[node])
            # Map each node to its new index in the subgraph
            sub_nodes[node] = len(sub_nodes)

        # Create a new Graph object for the subgraph with the necessary information
        subgraph = Graph(len(nodes), self.number_clients, self.number_edge_servers, self.number_cloud_servers, self.number_switch, self.clients, self.edge_servers, self.cloud_servers, sub_adj_matrix)

        return subgraph
