import numpy as np
from random import normalvariate
import networkx as nx
from networkx.readwrite import json_graph
import pymetis

def normdist_param(mean, std_dev, round=2):
    '''
        Generating normal dist link 
        param for mininet
    '''
    return round(np.random.normal(mean, std_dev))

# Normal choice
# https://stackoverflow.com/questions/35472461/select-one-element-from-a-list-using-python-following-the-normal-distribution
def normdist_array_genparam(numbers, mean=None, stddev=None):
    if mean is None:
        # if mean is not specified, use center of list
        mean = (len(numbers) - 1) / 2

    if stddev is None:
        # if stddev is not specified, let list be -3 .. +3 standard deviations
        stddev = len(numbers) / 6

    while True:
        index = int(normalvariate(mean, stddev) + 0.5)
        if 0 <= index < len(numbers):
            return numbers[index]

# def gen_loss(loss_numbers = [0, 1, 2, 4, 5, 7] 
#              p_arr = [0.37, 0.23, 0.15, 0.12, 0.08, 0.05]):
#     return np.random.choice(
#                         [0, 1, 2, 4, 5, 7],
#                         p=[0.37, 0.23, 0.15, 0.12, 0.08, 0.05]
#                     )

def read_graph_file(filename):
    try:
        graph = nx.read_graphml(filename)
    except nx.NetworkXError:
        try:
            graph = nx.read_gexf(filename)
        except nx.NetworkXError:
            try:
                graph = nx.read_edgelist(filename)
            except nx.NetworkXError:
                try:
                    # Read from json file
                    graph = json_graph.node_link_graph(filename)
                except nx.NetworkXError:
                    return "Error: Unsupported file format"
    return graph

def generate_adjlist(graph: nx.DiGraph, to_int=True) -> list[np.ndarray]:
    '''
        Input: take a networkx graph object
        Return: list of ndarray contain each each part
        of divided graph.
        Ex: [array([1, 5]), array([2, 3]), array([0, 4])]
    '''
    adj_list = []
    for _, nbrs in graph.adjacency():
        node_list = []
        for node, _ in nbrs.items():
            if to_int:
                node_list.append(int(node))
            else:
                node_list.append(node)
        adj_list.append(node_list)
    return adj_list

def part_graph(adj_list, num_parts):
    n_cuts, membership = pymetis.part_graph(num_parts, adjacency=adj_list)
    parts = []
    for i in range(num_parts):
        parts.append(np.argwhere(np.array(membership) == i).ravel())
    return parts

