from routingapp.compare_algorithm.sec_morl_multipolicy.env import SDN_Env
from routingapp.compare_algorithm.sec_morl_multipolicy.train import Actor, Critic
import os
import torch
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from routingapp.compare_algorithm.sec_morl_multipolicy.network import conv_mlp_net
from paretoset import paretoset
import pandas as pd

is_gpu_default = torch.cuda.is_available()
cloud_num = 1
edge_num = 1
expn = 'exp1'
config = 'multi-edge'
lr, epoch, batch_size = 1e-6, 1, 1024 * 4
# Load các mô hình đã huấn luyện từ w00 đến w100
trained_models = {}

for wi in range(100, -1, -1):
    actor = Actor(is_gpu=is_gpu_default)
    critic = Critic(is_gpu=is_gpu_default)
    
    actor_file_path = f'save/pth-e{edge_num}/cloud{cloud_num}/{expn}/w{wi:03d}/ep{epoch:02d}-actor.pth'
    critic_file_path = f'save/pth-e{edge_num}/cloud{cloud_num}/{expn}/w{wi:03d}/ep{epoch:02d}-critic.pth'
    
    if os.path.exists(actor_file_path) and os.path.exists(critic_file_path):
        actor.load_model(actor_file_path)
        critic.load_model(critic_file_path)
        trained_models[wi] = (actor, critic)
    else:
        # Thực hiện xử lý nếu file không tồn tại, ví dụ: thông báo hoặc pass
        pass
# Tạo môi trường không huấn luyện với edge_num và cloud_num mong muốn
untrained_env = SDN_Env(conf_name=config, w=0.5, fc=4e9, fe=2e9, edge_num=edge_num, cloud_num=cloud_num)

# List to store solutions from all episodes for each wi
train_wi_delay_solutions = []
train_wi_link_utilisation_solutions = []
untrained_wi_delay_solutions = []
untrained_wi_link_utilisation_solutions = []

# Collect solutions from all episodes for each wi
for wi, (actor, critic) in trained_models.items():
    env = SDN_Env(conf_name=config, w=wi / 100.0, fc=4e9, fe=2e9, edge_num=edge_num, cloud_num=cloud_num)
    train_delay_solutions = []
    train_link_utilisation_solutions = []
    untrained_delay_solutions = []
    untrained_link_utilisation_solutions = []
    for _ in range(1):  # Number of episodes
        # For trained models
        obs = env.reset()
        done = False
        while not done:
            # Choose actions using the actor model
            action, _ = actor(torch.FloatTensor(obs))
            # print(action.detach().numpy())
            # Perform actions and observe next state and reward
            next_obs, _, done, _ = env.step(action.detach().numpy())
            # Update current observation
            obs = next_obs


        delay, link_utilisation = env.estimate_performance()
        train_delay_solutions.append(delay)
        train_link_utilisation_solutions.append(link_utilisation)
        # For untrained models
        obs = untrained_env.reset()
        done = False
        untrained_actor = Actor(is_gpu=is_gpu_default)
        untrained_critic = Critic(is_gpu=is_gpu_default)
        untrained_episode_solutions = []
        while not done:
            # Choose actions using the actor model
            action, _ = actor(torch.FloatTensor(obs))
            # print(action.detach().numpy())
            # Perform actions and observe next state and reward
            next_obs, _, done, _ = env.step(action.detach().numpy())
            # Update current observation
            obs = next_obs
        delay, link_utilisation = untrained_env.estimate_performance()
        untrained_delay_solutions.append(delay)
        untrained_link_utilisation_solutions.append(link_utilisation)    
    train_wi_delay_solutions.append(np.mean(train_delay_solutions, axis=0))
    train_wi_link_utilisation_solutions.append(np.mean(train_link_utilisation_solutions, axis=0))
    untrained_wi_delay_solutions.append(np.mean(untrained_delay_solutions, axis=0))
    untrained_wi_link_utilisation_solutions.append(np.mean(untrained_link_utilisation_solutions, axis=0))

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
# Compute the Pareto front for all solutions
trained_all_mask = paretoset(train_solutions, sense=["min", "min"])
untrained_all_mask = paretoset(untrained_solutions, sense=["min", "min"])
# Filter the list of solutions, keeping only the non-dominated solutions
trained_efficient_solutions = train_solutions[trained_all_mask]
untrained_efficient_solutions = untrained_solutions[untrained_all_mask]
trained_pareto_delay = []
trained_pareto_link_utilisation = []
untrained_pareto_delay = []
untrained_pareto_link_utilisation = []
# Extract delay and link utilization for trained efficient solutions
for index, row in trained_efficient_solutions.iterrows():
    trained_pareto_delay.append(row['delay'])
    trained_pareto_link_utilisation.append(row['link_utilisation'])
for index, row in untrained_efficient_solutions.iterrows():
    untrained_pareto_delay.append(row['delay'])
    untrained_pareto_link_utilisation.append(row['link_utilisation'])
# Scatter plot comparison
plt.figure(figsize=(8, 6))
plt.scatter(trained_pareto_delay, trained_pareto_link_utilisation, color='blue', label='Trained')
plt.scatter(untrained_pareto_delay, untrained_pareto_link_utilisation, color='red', label='Untrained')
plt.xlabel('Delay (s)')
plt.ylabel('Link Utilization (Mbps)')
plt.title('Comparison: Trained vs Untrained Pareto Front Models')
plt.grid(True)
plt.legend()
plt.show()