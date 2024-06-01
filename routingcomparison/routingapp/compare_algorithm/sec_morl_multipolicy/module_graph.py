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
        self.predict_link_utilization = np.zeros((self.number_nodes+1, self.number_nodes+1))

    def updateGraph(self, delay_list, loss_list, bandwidth_list, link_utilization_list):
        for a in delay_list:
            self.predict_delay[a[0]][a[1]] = a[2]
        for a in loss_list:
            self.predict_loss[a[0]][a[1]] = a[2]
        for a in bandwidth_list:
            self.predict_bandwidth[a[0]][a[1]] = a[2]
        for a in link_utilization_list:
            self.predict_link_utilization[a[0]][a[1]] = a[2]

    def subgraph(self, nodes):
            """
            Create a subgraph from the original graph based on the provided list of nodes.
            Returns:
                Graph: The subgraph containing the specified nodes.
            """
            # Initialize an empty list to hold the adjacency matrix of the subgraph
            sub_adj_matrix = []
            # Initialize an empty dictionary to map nodes to their new indices in the subgraph
            sub_nodes = {}

            # Create a new adjacency matrix for the subgraph
            for node in nodes:
                # Check if the node exists in the original graph
                if node < len(self.adj_matrix):
                    # Append the corresponding row from the original adjacency matrix to the subgraph adjacency matrix
                    sub_adj_matrix.append(self.adj_matrix[node])
                    # Map each node to its new index in the subgraph
                    sub_nodes[node] = len(sub_nodes)
            # Add the node to the subgraph adjacency matrix if the node exist in adjacency matrix but not in the nodes list
            for node in range(len(self.adj_matrix)):
                if node not in sub_nodes:
                    sub_adj_matrix.append([-1] * len(self.adj_matrix))
                    sub_nodes[node] = len(sub_nodes)
            # Create a new Graph object for the subgraph with the necessary information
            subgraph = Graph(
                len(sub_nodes),
                len([node for node in self.clients if node in nodes]),
                self.number_edge_servers,
                self.number_cloud_servers,
                len([node for node in range(self.number_nodes) if node not in self.clients and node not in self.edge_servers and node not in self.cloud_servers]),
                [node for node in self.clients if node in nodes],
                self.edge_servers,
                self.cloud_servers,
                sub_adj_matrix
            )

            # Update delay, loss, and bandwidth information to match the new node indices (check the avalability of client, edge server, cloud server in the subgraph)
            for i in range(self.number_nodes + 1):
                for j in range(self.number_nodes + 1):
                    if i in sub_nodes and j in sub_nodes:
                        subgraph.predict_delay[sub_nodes[i]][sub_nodes[j]] = self.predict_delay[i][j]
                        subgraph.predict_loss[sub_nodes[i]][sub_nodes[j]] = self.predict_loss[i][j]
                        subgraph.predict_bandwidth[sub_nodes[i]][sub_nodes[j]] = self.predict_bandwidth[i][j]
            # Ensure the node and edge server are not in the initial of the subgraph has delay, loss, bandwidth, link utilization equal to 0
            
            return subgraph