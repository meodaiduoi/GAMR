import numpy as np
class Graph:
    def __init__(self, number_nodes, number_clients, number_servers, number_switch, clients, servers, adj_matrix):
        self.number_nodes = number_nodes
        self.number_clients = number_clients
        self.number_servers = number_servers
        self.number_switch = number_switch
        self.clients = clients
        self.servers = servers
        self.adj_matrix = adj_matrix
        self.predict_delay = np.zeros((self.number_nodes+1, self.number_nodes+1))
        self.predict_loss = np.zeros((self.number_nodes+1, self.number_nodes+1))
        self.predict_bandwidth = np.zeros((self.number_nodes+1, self.number_nodes+1))
    #delay_list includes (first_node, second_node, new_delay) tuple
    #loss_list include (first_node, second_node, new_delay) tuple
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