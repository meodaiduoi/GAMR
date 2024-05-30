from routingapp.compare_algorithm.sec_morl_multipolicy.rl import SDN_Env
import numpy as np
import random 
from collections import deque
from routingapp.compare_algorithm.sec_morl_multipolicy.train import Actor, Critic, is_gpu_default, expn, epoch
import os
import torch 
class Function:
    def bfs(self, graph, start, goal):
        visited = set()  # Danh sách các đỉnh đã được duyệt
        queue = deque([(start, [start])])  # Hàng đợi chứa cặp (đỉnh, đường đi từ nguồn tới đỉnh)

        while queue:
            node, path = queue.popleft()  # Lấy đỉnh đầu tiên từ hàng đợi và đường đi tới đỉnh
            if node not in visited:
                visited.add(node)
                if node == goal:
                    return path  # Trả về đường đi từ nguồn tới đích
                neighbors = graph[node]
                for neighbor in neighbors:
                    if neighbor not in visited:
                        queue.append((neighbor, path + [neighbor]))  # Thêm các đỉnh kề chưa duyệt vào hàng đợi với đường đi tới đỉnh đó

        return None  # Nếu không tìm thấy đường đi từ nguồn tới đích

    def cal_delay(self, path, delay_predict_matrix ):
        delay = 0
        for i in range (0, len(path)-1):
            delay = delay + delay_predict_matrix[path[i]][path[i+1]]
        return delay
    
    
    def cal_bandwidth(self, path, band_width_predict_matrix):
        bandwidth = 10000
        for i in range(0, len(path)-1):
            bandwidth  = min(bandwidth, band_width_predict_matrix[path[i]][path[i+1]])
        
        return bandwidth
    
    def cal_packetLoss(self, path, loss_predict_matrix):
        loss = 0
        for i in range(0, len(path)-1):
            loss = loss + (1-loss)*loss_predict_matrix[path[i]][path[i+1]]
        
        return loss
    
    def cal_linkutilization(self, path, link_utilization_matrix):
        link_utilization = 0
        for i in range(0, len(path)-1):
            link_utilization = max(link_utilization, link_utilization_matrix[path[i]][path[i+1]])
        return link_utilization
    
    def update_weight_matrix(self, delay, lossPacket, i, j, new_delay, new_lossPacket):
        delay[i][j] = new_delay
        lossPacket[i][j] = new_lossPacket
    # Generate a random path from src_node to dst_node   
    def createRandom(self, src_node, dst_node, adj_matrix):
        OK = True
        while OK :
            router = []
            router.append(src_node)
            node_number = len(adj_matrix)
            visited_node = []
            visited_node.append(src_node)
            for j in range (1, node_number):
                adj_node = []
                for a in adj_matrix[router[j-1]]:
                    if a not in visited_node:
                        adj_node.append(a)
                if len(adj_node) ==0:
                    break
                temp = random.choice(adj_node)
                router.append(temp)
                visited_node.append(temp)
                if temp == dst_node:
                    OK = False
                    break
        return (src_node, dst_node, router)

    #location is crossing location
    def repairPath(self, path, location):
        i = len(path)-2 
        pos = 0
        while i > location:
            if path[i] in path[:location]:
                pos  = path[: location].index(path[i])
                break
            i = i-1
        if pos != 0:
            del path[pos:i]
    #repair anypath
    def repairPath2(self, path):
        i = 1
        while i < len(path)-1:
            if path[i] in path[i+1:]:
                pos = path[i+1:-1].index(path[i])
                del path[i: pos]
            i = i+1
        return path
    def crossPath(self, path1, path2):
        # crossing point of (path1, path2)
        cross_path =[]
        path1_len = len(path1)
        for i in path1[1: path1_len-1]:
            if i in path2:
                cross_path.append(i)
        if len(cross_path) == 0:
            return path1, path2
        cross_point  = random.choice(cross_path)
        #loc1, loc2 are location of cross_point in path1, path2
        loc1 = path1.index(cross_point)
        loc2 = path2.index(cross_point)
        #Generate offspring
        off1 = path1[: loc1+1]
        off2 = path2[: loc2+1]
        off1.extend(path2[loc2+1:])
        off2.extend(path1[loc1+1:])
        self.repairPath(off1, loc1)
        self.repairPath(off2, loc2)
        
        return off1, off2
    
    #Generate a path by inserting a node
    def createPath_insert(self, router, adj_matrix ):
        path_index = np.arange(0, len(router) -1)
        path_index = list(path_index)
        new_path = []
        while len(path_index) > 0:
            #loc_index is index of inserted point
            loc_index = random.choice(path_index)
            #adj_node includes point that adj of path[loc_index] and path[loc_index +1]
            adj_node =[]
            path_index.remove(loc_index)
            for a in adj_matrix[router[loc_index]]:
                if (a in adj_matrix[router[loc_index+1]]) and (a!=router[0]) and (a!=router[-1]) and (a not in router):
                    adj_node.append(a)
            if len(adj_node) != 0:
                insert_node = random.choice(adj_node)
                new_path.extend(router[: loc_index+1])
                new_path.append(insert_node)
                new_path.extend(router[loc_index+1:])
                return new_path
        return router
    
    # selected path
    def select_solution(self, solutions):
        solution_number = len(solutions)
        same_link = np.zeros(solution_number, dtype=int)
        for i in range (solution_number):
            link = []
            for path in solutions[i]:
                for j in range (0, len(path[2])-1):
                    if (path[2][j], path[2][j+1]) in link:
                        same_link[i] = same_link[i] + 1
                    else:
                        link.append((path[2][j], path[2][j+1]))
                        link.append((path[2][j+1], path[2][j]))
        same_link = list(same_link)
        index = same_link.index(min(same_link))
        return solutions[index]     
    
    def generate_solutions(graph, function, request):
        # Generate solutions
        solutions = []
        delays = []
        link_utilisations = []
        # Load trained models from w00 to w100
        trained_models = {}

        for wi in range(100, -1, -1):
            actor = Actor(is_gpu=is_gpu_default)
            critic = Critic(is_gpu=is_gpu_default)
            
            actor_file_path = f'save/pth-e{graph.number_edge_servers}/cloud{graph.number_cloud_servers}/{expn}/w{wi:03d}/ep{epoch:02d}-actor.pth'
            critic_file_path = f'save/pth-e{graph.number_edge_servers}/cloud{graph.number_cloud_servers}/{expn}/w{wi:03d}/ep{epoch:02d}-critic.pth'
            
            if os.path.exists(actor_file_path) and os.path.exists(critic_file_path):
                actor.load_model(actor_file_path)
                critic.load_model(critic_file_path)
                trained_models[wi] = (actor, critic)
            else:
                # Passing when not finding a trained model
                pass  

        # Collect solutions from all episodes for each wi
        for wi, (actor, critic) in trained_models.items():
            env = SDN_Env(graph=graph, function = function, request=request, w=wi / 100.0)
            for _ in range(1):  # Number of episodes
                # For trained models
                obs = env.reset()
                done = False
                while not done:
                    # Choose actions using the actor model
                    action, _ = actor(torch.FloatTensor(obs))
                    # Perform actions and observe next state and reward
                    next_obs, _, done, info = env.step(action.detach().numpy())
                    # Update current observation
                    obs = next_obs
                # Estimate the performance of the trained model
                avg_delay, avg_link_utilisation = env.estimate_performance()

                # Append to lists
                delays.append(avg_delay)
                link_utilisations.append(avg_link_utilisation)
            # Save the solution
            solutions = env.get_path()
        return solutions
            