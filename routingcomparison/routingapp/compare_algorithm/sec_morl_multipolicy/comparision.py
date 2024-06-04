from rl import SDN_Env
import gym
from train import Actor, Critic, sdn_net
import os
import torch
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from network import conv_mlp_net
from paretoset import paretoset
import pandas as pd
from module_graph import Graph
from module_function import Function
import os
import json
# import default Actor, Critic of tianshou
from tianshou.utils.net.discrete import Actor as UntrainedActor, Critic as UntrainedCritic
import matplotlib
matplotlib.use('Qt5Agg')  # Use the Qt5Agg backend for interactive plotting
import matplotlib.pyplot as plt

is_gpu_default = torch.cuda.is_available()
cloud_num = 1
edge_num = 4
expn = 'exp1'
config = 'multi-edge'
lr, epoch, batch_size = 1e-6, 1, 1024 * 4
# Load các mô hình đã huấn luyện từ w00 đến w100
trained_models = {}

def read_data(filename):
    with open(filename) as f:
        data = json.load(f)
    return data

# DFS function to find paths from source to destination
def dfs(graph, start, goal):
    visited = set()  # List of visited nodes
    # Stack containing pairs (node, path from source to node)
    stack = [(start, [start])]

    while stack:
        node, path = stack.pop()  # Get the last node from the stack and the path to it
        if node not in visited:
            visited.add(node)
            if node == goal:
                return path  # Return the path from source to destination
            # Access neighbors from the adjacency matrix of the graph
            neighbors = graph.adj_matrix[node]
            # Traverse neighbors in reverse order to use stack
            for neighbor in reversed(neighbors):
                if neighbor not in visited:
                    # Add unvisited neighbors to stack with path to that node
                    stack.append((neighbor, path + [neighbor]))

    return None  # If no path from source to destination is found

# Read data from JSON file and define graph object


def graph_generate(filename):
    # Read data from JSON file
    data = read_data(filename)
    nodes = data['nodes']
    edge_servers = data['edge_server']
    cloud_servers = data['cloud_server']
    clients = data['client']
    edges = data['edges']
    adj_matrix = [[] for _ in range(len(nodes))]
    for edge in edges:
        adj_matrix[edge[0]].append(edge[1])
        adj_matrix[edge[1]].append(edge[0])
    # Define the graph object
    graph = Graph(len(nodes), len(clients), len(edge_servers), len(
        cloud_servers), len(clients), clients, edge_servers, cloud_servers, adj_matrix)

    # Iterate through each scenario in the data
    scenario_list = data['scenario']
    for scenario in scenario_list:
        sum_delay_topo = 0
        delay_update = scenario["delay"]
        for delay in delay_update:
            sum_delay_topo = sum_delay_topo + delay[2]
        bandwidth_update = scenario["bandwidth"]
        loss_update = scenario["loss"]
        request = scenario["request"]
        link_utilization_list = scenario["link_utilization"]
        # print("Request: ", request)
        # Update the graph with delay, loss, and bandwidth information
        graph.updateGraph(delay_update, loss_update,
                          bandwidth_update, link_utilization_list)

        # print(graph.adj_matrix, graph.number_nodes, graph.number_edge_servers, graph.number_clients, graph.number_cloud_servers)
        # Generate the promising paths using DFS
        promising_paths = []
        request_list = []
        # print(request)
        for src, dst in request:
            # print(src, dst)
            path = dfs(graph, src, dst)
            if path:
                promising_paths.append(path)
            # print(promising_paths)

            # Create a subgraph containing all paths in the promising paths
            promising_nodes = set()
            for path in promising_paths:
                # print(path)
                promising_nodes.update(path)
            # print(promising_nodes)
            promising_graph = graph.subgraph(list(promising_nodes))

            # Update src and dst in the request to match the new node indices
            promising_nodes_list = list(promising_nodes)

            # Update src and dst in the request to match the new node indices
            request_list.append([promising_nodes_list.index(
                src), promising_nodes_list.index(dst)])

            # print(request)
            # print(promising_graph.number_nodes, promising_graph.number_edge_servers, promising_graph.number_clients, promising_graph.number_cloud_servers)

    return graph, request_list

def generate_file(data_path):
    # Generate the graph object
    graph, request = graph_generate(data_path)

    # Initialize the function object
    func = Function()

    # Use the trained models to generate solutions
    return graph, func, request
def compare(test_graph, func, test_request):
    trained_models = {}
    for wi in range(0, 101, 2):
        actor = Actor(is_gpu=is_gpu_default, edge_num = test_graph.number_edge_servers, cloud_num = test_graph.number_cloud_servers)
        critic = Critic(is_gpu=is_gpu_default, edge_num = test_graph.number_edge_servers, cloud_num = test_graph.number_cloud_servers)
        
        actor_file_path = f'save/pth-e{edge_num}/cloud{cloud_num}/{expn}/w{wi:03d}/ep{epoch:02d}-actor.pth'
        critic_file_path = f'save/pth-e{edge_num}/cloud{cloud_num}/{expn}/w{wi:03d}/ep{epoch:02d}-critic.pth'
        
        if os.path.exists(actor_file_path) and os.path.exists(critic_file_path):
            actor.load_model(actor_file_path)
            critic.load_model(critic_file_path)
            trained_models[wi] = (actor, critic)
        else:
            # Thực hiện xử lý nếu file không tồn tại, ví dụ: thông báo hoặc pass
            pass
    
    train_wi_delay_solutions, train_wi_link_utilisation_solutions, untrained_wi_delay_solutions, untrained_wi_link_utilisation_solutions = collect_solutions(test_graph, func, test_request, trained_models)
    
    train_solutions = pd.DataFrame(
        {
            "delay": train_wi_delay_solutions,
            "link_utilisation": train_wi_link_utilisation_solutions,
        }
    )
    untrained_solutions = pd.DataFrame(
        {
            "delay": untrained_wi_delay_solutions,
            "link_utilisation": untrained_wi_link_utilisation_solutions,
        }
    )
    trained_pareto_delay, trained_pareto_link_utilisation = extract_pareto_solutions(train_solutions)
    untrained_pareto_delay, untrained_pareto_link_utilisation = extract_pareto_solutions(untrained_solutions)
    
    return trained_pareto_delay, trained_pareto_link_utilisation, untrained_pareto_delay, untrained_pareto_link_utilisation

def collect_solutions(test_graph, func, test_request, trained_models):
    train_wi_delay_solutions = []
    train_wi_link_utilisation_solutions = []
    untrained_wi_delay_solutions = []
    untrained_wi_link_utilisation_solutions = []

    for wi, (actor, critic) in trained_models.items():
        env = SDN_Env(graph = test_graph, function = func, request = test_request, w=wi / 100.0)
        train_delay_solutions = []
        train_link_utilisation_solutions = []
        untrained_delay_solutions = []
        untrained_link_utilisation_solutions = []
        
        for _ in range(1):  # Number of episodes
            obs = env.reset()
            done = False
            
            while not done:
                actions, _ = actor(torch.FloatTensor(obs))
                action = np.argmax(actions.cpu().detach().numpy())
                next_obs, _, done, _ = env.step(action)
                obs = next_obs

            delay, link_utilisation = env.estimate_performance()
            train_delay_solutions.append(delay)
            train_link_utilisation_solutions.append(link_utilisation)
            
            untrained_env = SDN_Env(graph = test_graph, function = func, request = test_request, w= (wi-1) / 100.0)
            obs = untrained_env.reset()
            done = False
            untrained_episode_solutions = []
            
            while not done:
                actions, _ = actor(torch.FloatTensor(obs))
                action = np.argmax(actions.cpu().detach().numpy())
                next_obs, _, done, _ = untrained_env.step(action)
                obs = next_obs
                
            delay, link_utilisation = untrained_env.estimate_performance()
            untrained_delay_solutions.append(delay)
            untrained_link_utilisation_solutions.append(link_utilisation)    
        
        train_wi_delay_solutions.append(np.sum(train_delay_solutions, axis=0))
        train_wi_link_utilisation_solutions.append(np.sum(train_link_utilisation_solutions, axis=0))
        untrained_wi_delay_solutions.append(np.sum(untrained_delay_solutions, axis=0))
        untrained_wi_link_utilisation_solutions.append(np.sum(untrained_link_utilisation_solutions, axis=0))
    
    return train_wi_delay_solutions, train_wi_link_utilisation_solutions, untrained_wi_delay_solutions, untrained_wi_link_utilisation_solutions

def extract_pareto_solutions(solutions):
    all_mask = paretoset(solutions, sense=["min", "min"])
    efficient_solutions = solutions[all_mask]
    pareto_delay = []
    pareto_link_utilisation = []
    
    for index, row in efficient_solutions.iterrows():
        pareto_delay.append(row['delay'])
        pareto_link_utilisation.append(row['link_utilisation'])
    
    return pareto_delay, pareto_link_utilisation


# Load dữ liệu từ file
graph, func, request = generate_file(r"/home/ad/RoutingComparasion/RoutingComparation/routingcomparison/routingapp/compare_algorithm/data/chinanet/4_edge_cloud_server.json")
trained_pareto_delay,trained_pareto_link_utilisation, untrained_pareto_delay, untrained_pareto_link_utilisation = compare(graph, func, request)

# # Scatter plot comparison
# plt.figure(figsize=(8, 6))
# plt.scatter(trained_pareto_delay, trained_pareto_link_utilisation, color='blue', label='Trained')
# plt.scatter(untrained_pareto_delay, untrained_pareto_link_utilisation, color='red', label='Untrained')
# plt.xlabel('Delay (s)')
# plt.ylabel('Link Utilization (Mbps)')
# plt.title('Comparison: Trained vs Untrained Pareto Front Models')
# plt.grid(True)
# plt.legend()
# plt.show()