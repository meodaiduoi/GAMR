import numpy as np
from random import normalvariate
import networkx as nx
from networkx.readwrite import json_graph

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