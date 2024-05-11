from routingapp.compare_algorithm.sec_morl_multipolicy.function_dijkstra import dijkstra, routing_k

from copy import deepcopy
import numpy as np
import json
import gym
from gym.spaces import MultiDiscrete
        
class SDN_Env(gym.Env):
    def __init__(self, graph, function, request, w=1.0):
        super(SDN_Env, self).__init__()
        self.w = w
        self.graph = graph
        self.function = function
        self.request = request
        self.predict_delay = graph.predict_delay
        self.predict_loss = graph.predict_loss
        self.predict_bandwidth = graph.predict_bandwidth
        self.number_clients = graph.number_clients if graph is not None else 0
        self.number_edge_servers = graph.number_edge_servers if graph is not None else 0
        self.number_cloud_servers = graph.number_cloud_servers if graph is not None else 0
        self.edge_servers = sorted(graph.edge_servers) if graph is not None else None
        self.cloud_servers = sorted(graph.cloud_servers) if graph is not None else None
        self.request = request
        self.step_cnt = 0
        self.Tmax = 100
        # Bounds are set based on the number of edge and cloud servers
        low_bound = np.zeros(self.number_edge_servers + self.number_cloud_servers)
        high_bound = np.ones(self.number_edge_servers + self.number_cloud_servers)
        self.action_space = gym.spaces.Box(low=low_bound, high=high_bound, shape=(self.number_edge_servers + self.number_cloud_servers,))

        # Initialize the environment
        self.reset()  

    def reset(self, **kwargs):
        # Reset environment variables
        self.step_cnt = 0
        self.task_size = 0
        self.task_user_id = 0
        self.rew_t = 0
        self.rew_lu = 0
        self.invalid_act_flag = False
        self.unassigned_task_list = []

        self.edge_lists = []
        self.cloud_lists = []
        # Set the action space size based on the number of edge servers
        self.action_space = gym.spaces.Box(low=0, high=1, shape=(self.number_edge_servers + self.number_cloud_servers,))

        # Set environment flags and variables
        self.done = False
        self.reward_buff = []

        for _ in range(self.number_edge_servers):
            self.edge_lists.append([])
        for _ in range(self.number_cloud_servers):
            self.cloud_lists.append([])

        # Print the size of the state (ra)
        return self.get_obs()

               
    def step(self, actions):
        # Kiểm tra xem môi trường đã kết thúc chưa
        assert self.done == False, 'environment already output done'
        self.step_cnt += 1  # Tăng bước thời gian lên 1
        finished_task = []  # Danh sách công việc đã hoàn thành
        edge_action = -1
        cloud_action = -1
        cloud_path = None
        edge_path = None
        des_path = None
        
        # Case 1: Choose the edge server with the highest probability
        if np.all(actions[:self.number_edge_servers] == 1):
            edge_action = np.argmax(actions[:self.number_edge_servers])
        # Case 2: Choose the cloud server with the highest probability
        elif np.all(actions[self.number_edge_servers:] == 1):
            cloud_action = np.argmax(actions[self.number_edge_servers:])
        # Case 3: Choose both edge and cloud servers
        else:
            edge_action = np.argmax(actions[:self.number_edge_servers])
            cloud_action = np.argmax(actions[self.number_edge_servers:])
        
        self.edge_action = edge_action
        self.cloud_action = cloud_action
        
        # print(f"Edge Action: {edge_action}, Cloud Action: {cloud_action}")    
        #####################################################
        # Assignment of tasks (Phân công công việc)
        the_task = {}
        the_task['start_step'] = self.step_cnt
        the_task['delay_time'] = 0
        the_task['link_utilisation'] = 0  # Initialize  link utilization
        
        print(f"Edge Action: {edge_action}, Cloud Action: {cloud_action}")    
        # Case 1: Routing task with both edge and cloud
        if (edge_action is not None) and (cloud_action is not None) and (0 <= edge_action < self.number_edge_servers) and (0 <= cloud_action < self.number_cloud_servers):
            # Routing task to the edge server
            e = edge_action
            the_task['to'] = e
            print(self.edge_servers, self.edge_servers[edge_action])
            edge_path = dijkstra(self.graph, 1, self.request[0], self.edge_servers[edge_action])
            edge_link_utilisation = self.function.cal_bandwidth(edge_path, self.predict_bandwidth)
            edge_delay = self.function.cal_delay(edge_path, self.predict_delay)
            the_task['link_utilisation'] += edge_link_utilisation
            the_task['off_delay'] += edge_delay
            self.edge_lists[e].append(the_task)
            
            # Uploading task to the cloud server
            c = cloud_action
            the_task['to'] = c
            cloud_path = dijkstra(self.graph, 1, self.edge_servers[edge_action], self.cloud_servers[cloud_action]) 
            des_path = dijkstra(self.graph, 1, self.cloud_servers[cloud_action], self.request[1])
            cloud_link_utilisation = self.function.cal_bandwidth(cloud_path, self.predict_bandwidth) + self.function.cal_bandwidth(des_path, self.predict_bandwidth)
            cloud_delay = self.function.cal_delay(cloud_path, self.predict_delay) + self.function.cal_delay(des_path, self.predict_delay)
            the_task['link_utilisation'] += cloud_link_utilisation
            the_task['off_delay'] += cloud_delay
            self.cloud_lists[c].append(the_task)
        else:
            # Case 2: Routing task with edge server 
            if (edge_action is not None) and (0 <= edge_action < self.number_edge_servers):
                e = edge_action
                the_task['to'] = e
                edge_path = dijkstra(self.graph, 1, self.request[0], self.edge_servers[edge_action]) 
                des_path = dijkstra(self.graph, 1, self.edge_servers[edge_action], self.request[1])
                edge_link_utilisation = self.function.cal_bandwidth(edge_path, self.predict_bandwidth) + self.function.cal_bandwidth(des_path, self.predict_bandwidth)
                edge_delay = self.function.cal_delay(edge_path, self.predict_delay) + self.function.cal_delay(des_path, self.predict_delay)
                the_task['link_utilisation'] += edge_link_utilisation
                the_task['off_delay'] += edge_delay
                self.edge_lists[e].append(the_task)
            # Case 3: Routing task with edge server 
            if (cloud_action is not None) and (0 <= cloud_action < self.number_cloud_servers):
                c = cloud_action
                the_task['to'] = c
                cloud_path = dijkstra(self.graph, 1, self.request[0], self.cloud_servers[cloud_action]) 
                des_path = dijkstra(self.graph, 1, self.cloud_servers[cloud_action], self.request[1])
                cloud_link_utilisation = self.function.cal_bandwidth(cloud_path, self.predict_bandwidth) + self.function.cal_bandwidth(des_path, self.predict_bandwidth)
                cloud_delay = self.function.cal_delay(cloud_path, self.predict_delay) + self.function.cal_delay(des_path, self.predict_delay)
                the_task['link_utilisation'] += cloud_link_utilisation
                the_task['off_delay'] += cloud_delay
                self.cloud_lists[c].append(the_task)
            else:
                assert (0 <= edge_action < self.number_edge_servers or 0 <= cloud_action < self.number_cloud_servers), f'server selection action is invalid: {edge_action}, {cloud_action}'
                # Handle invalid action
                self.invalid_act_flag = True
                    
            self.rew_t, self.rew_lu = self.estimate_rew()
        #####################################################
        # Done condition (Điều kiện kết thúc)
        if (self.step_cnt >= self.Tmax):
            self.done = True
        done = self.done

        #####################################################
        # Observation encoding (Mã hóa quan sát)
        obs = self.get_obs()

        #####################################################
        # Reward calculation (Tính toán thưởng)
        reward = self.get_reward(finished_task)

        # # Print the size of the action
        # print(f"Size of Action: {actions}")

        # # Print the size of the reward
        # print(f"Size of Reward: {reward}")
        #####################################################
        # Additional information (Thông tin bổ sung)
        info = {}
        # Create the complete_path from edge_path and cloud_path (if both are not None)
        if edge_path is not None and cloud_path is not None and des_path is not None:
            complete_path = edge_path + cloud_path[1:]  + des_path[1:] 
            info['complete_path'] = complete_path
        # If only edge_path is not None, store it as complete_path
        elif edge_path is not None and des_path is not None:
            info['complete_path'] = edge_path + des_path[1:] 
        # If only cloud_path is not None, store it as complete_path
        elif cloud_path is not None and des_path is not None:
            info['complete_path'] = cloud_path + des_path[1:] 
        else: 
            raise ValueError('No path has been founded!')
        return obs, reward, done, info

    
    def get_obs(self):
        obs = {}
        servers = []
        for _ in range(self.number_edge_servers):
            edge = []
            edge.append(1.0)
            edge.append(float(self.number_edge_servers))
            edge.append(float(1 - self.done))
            
            # # Get the path of the selected edge server 
            # edge_path = dijkstra(self.graph, 1, self.request[0], self.edge_servers[ii]) + dijkstra(self.graph, 1, self.edge_servers[ii], self.request[1])
            
            # # Append the path information to the observation
            # edge.append(edge_path)
            
            # edge = np.concatenate([np.array(edge, dtype=float)], axis=0)
            servers.append(edge)

        for _ in range(self.number_cloud_servers):
            cloud = []
            cloud.append(1.0)
            cloud.append(float(self.number_cloud_servers))
            cloud.append(float(1 - self.done))
            
            # # Get the path of the selected cloud server 
            # cloud_path = dijkstra(self.graph, 1, self.request[0], self.cloud_servers[ii]) + dijkstra(self.graph, 1, self.cloud_servers[ii], self.request[1])
            
            # # Append the path information to the observation
            # cloud.append(cloud_path)
            
            # cloud = np.concatenate([np.array(cloud, dtype=float)], axis=0)
            servers.append(cloud)
        # Swap axes to get the shape (features, servers)
        obs['servers'] = np.array(servers).swapaxes(0, 1)

        # Combine edge and cloud observations into a single state dictionary
        re = obs['servers']
        return re

    def estimate_rew(self):
        # Initialize reward components
        reward_dt = 0
        reward_dlu = 0
        
        edge_action = self.edge_action
        cloud_action = self.cloud_action
        
        the_task = {}
        the_task['delay_time'] = 0
        the_task['link_utilisation'] = 0
        
        if 0 <= edge_action < self.number_edge_servers:
            # Chosen action is an edge server
            for task in self.edge_lists[edge_action]:
                the_task['delay_time'] += task['off_delay']
                the_task['link_utilisation'] += task['link_utilisation']
        if 0 <= cloud_action < self.number_cloud_servers:
            # Chosen action is a cloud server
            for task in self.cloud_lists[cloud_action]:
                the_task['delay_time'] += task['off_delay']
                the_task['link_utilisation'] += task['link_utilisation']
        
        # # Estimate rewards based on task information       
        # if self.task_size > 0:
        #     # If there are tasks present, estimate rewards based on task information
        #     reward_dt = -the_task['delay_time'] * 0.01
        #     reward_dlu = -the_task['link_utilisation'] * 50
        # else:
        #     # If no tasks are present, set rewards to zero
        #     reward_dt = 0
        #     reward_dlu = 0
        
        reward_dt = -the_task['delay_time'] * 0.01
        reward_dlu = -the_task['link_utilisation'] * 50
        
        return reward_dt, reward_dlu
    
    def get_reward(self, finished_task):
        reward_dt, reward_dlu = self.estimate_rew()
        reward = self.w * reward_dt + (1.0 - self.w) * reward_dlu
        return reward

    def seed(self, seed=None):
        np.random.seed(seed)

    def render(self, mode='human'):
        # Implement rendering logic if needed
        pass

    
    def seed(self, seed=None):
        np.random.seed(seed)

    def render(self, mode='human'):
        # Implement rendering logic if needed
        pass
    def estimate_performance(self):
        total_delay = 0
        total_bandwidth_utilization = 0
        
        # Iterate over all tasks in the environment
        for task in self.edge_lists:
            total_delay += task['off_delay']  # Accumulate delay
            total_bandwidth_utilization += task['link_utilisation']  # Accumulate bandwidth utilization
        for task in self.cloud_lists:
            total_delay += task['off_delay']  # Accumulate delay
            total_bandwidth_utilization += task['link_utilisation'] # Accumulate bandwidth utilization
            
        return total_delay, total_bandwidth_utilization