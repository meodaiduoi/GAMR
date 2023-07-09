from .module_individual import Individual

import random

class Population:
    def __init__(self):
        self.indi_list = []
        self.ParetoFront = []
    # k request
    # def generate_population(self, graph, function, number_indi, k, pair_list ):
    #     for i in range(0, number_indi):
    #         indi = Individual()
    #         indi.generateRandom(k, pair_list, function, graph.adj_matrix, graph.predict_delay, graph.predict_bandwidth, graph.predict_loss)
    #         self.indi_list.append((indi))
    def generate_population(self, graph, function, number_indi, k, pair_list, memSet):
        exist_server = []
        # mem_Set = {
        #     server: [(src, dst, router)]
        # }
        indi = Individual()
        delay_bfs =0
        loss_bfs = 0
        bandwidth_bfs = 0
        for pair in pair_list:
            path = function.bfs(graph.adj_matrix, pair[0], pair[1])
            delay_bfs = delay_bfs + function.cal_delay(path, graph.predict_delay)
            loss_bfs = loss_bfs + function.cal_packetLoss(path, graph.predict_loss)
            bandwidth_bfs = bandwidth_bfs + function.cal_bandwidth(path, graph.predict_bandwidth)
            indi.chromosome.append((pair[0], pair[1], path))
        delay_bfs = delay_bfs/k
        loss_bfs = loss_bfs/k
        bandwidth_bfs = -bandwidth_bfs/k
        indi.objectives.extend([delay_bfs, bandwidth_bfs, loss_bfs])
        self.indi_list.append(indi)
           
        for pair in pair_list:
            if pair[1] in memSet.server_set:
                exist_server.append(pair[1])
        for i in range(0, int(number_indi/5)):
            indi = Individual()
            map_server_path = {}
            for server in exist_server:
                server_path = random.choice(memSet.memset[server])
                map_server_path[server] = server_path
            indi.generateMemset(k, pair_list, exist_server, map_server_path, function, graph.adj_matrix, graph.predict_delay, graph.predict_bandwidth, graph.predict_loss)
            self.indi_list.append(indi)
        for i in range (0, int(4*number_indi/5)-1):
            indi = Individual()
            indi.generateRandom(k, pair_list, function, graph.adj_matrix, graph.predict_delay, graph.predict_bandwidth, graph.predict_loss)
            self.indi_list.append(indi)
        
    def crossIndividual(self, function, number_particips, delay_predict_matrix, loss_predict_matrix, band_width_predict_matrix):
        indi_couple = random.sample(self.indi_list, number_particips)
        parent1 = indi_couple[0]
        for other_indi in indi_couple[1:]:
            if other_indi.dominates(parent1):
                parent1 = other_indi
        indi_couple = random.sample(self.indi_list, number_particips)
        parent2 = indi_couple[0]
        for other_indi in indi_couple[1:]:
            if other_indi.dominates(parent2):
                parent2 = other_indi
        off1 = Individual()
        off2 = Individual()
        delay_mean1, loss_mean1, bandwidth_mean1 = 0,0,0
        delay_mean2, loss_mean2, bandwidth_mean2 = 0,0,0
        k = len(parent1.chromosome)
        for path1, path2 in zip(parent1.chromosome, parent2.chromosome):
            off1_router, off2_router = function.crossPath(path1[2], path2[2])
            off1_path = (path1[0], path1[1], off1_router)
            off2_path = (path2[0], path2[1], off2_router)
            off1.chromosome.append(off1_path)
            off2.chromosome.append(off2_path)
            predict_delay1 = function.cal_delay(off1_path[2], delay_predict_matrix)
            predict_bandwidth1 = function.cal_bandwidth(off1_path[2], band_width_predict_matrix)
            predict_lossPacket1 = function.cal_packetLoss(off1_path[2], loss_predict_matrix)
            delay_mean1 = delay_mean1 + predict_delay1
            loss_mean1 = loss_mean1 + predict_lossPacket1
            bandwidth_mean1 = bandwidth_mean1 + predict_bandwidth1
            off1.routing_objectives.append((predict_delay1, predict_bandwidth1, predict_lossPacket1))

            predict_delay2 = function.cal_delay(off2_path[2], delay_predict_matrix)
            predict_bandwidth2 = function.cal_bandwidth(off2_path[2], band_width_predict_matrix)
            predict_lossPacket2 = function.cal_packetLoss(off2_path[2], loss_predict_matrix)
            delay_mean2 = delay_mean2 + predict_delay2
            loss_mean2 = loss_mean2 + predict_lossPacket2
            bandwidth_mean2 = bandwidth_mean2 + predict_bandwidth2
            off2.routing_objectives.append((predict_delay2, predict_bandwidth2, predict_lossPacket2))
        
        delay_mean1 = delay_mean1/k
        loss_mean1 = loss_mean1/k
        #maximize bandwidth => minimize - bandwidth
        bandwidth_mean1 = - bandwidth_mean1/k
        off1.objectives.extend([delay_mean1, bandwidth_mean1, loss_mean1])

        delay_mean2 = delay_mean2/k
        loss_mean2 = loss_mean2/k
        #maximize bandwidth => minimize - bandwidth
        bandwidth_mean2 = - bandwidth_mean2/k
        off2.objectives.extend([delay_mean2, bandwidth_mean2, loss_mean2])
        return off1, off2                          
    
    def fast_nondominated_sort(self):
        self.ParetoFront = [[]]
        for individual in self.indi_list:
            individual.domination_count = 0
            individual.dominated_solutions = []
            for other_individual in self.indi_list:
                if individual.dominates(other_individual):
                    individual.dominated_solutions.append(other_individual)
                elif other_individual.dominates(individual):
                    individual.domination_count +=1
            if individual.domination_count ==0:
                individual.rank = 0
                self.ParetoFront[0].append(individual)
        i = 0
        while len(self.ParetoFront[i])>0:
            temp = []
            for individual in self.ParetoFront[i]:
                for other_individual in individual.dominated_solutions:
                    other_individual.domination_count -=1
                    if other_individual.domination_count == 0:
                        other_individual.rank =i+ 1
                        temp.append(other_individual)
            i = i + 1
            self.ParetoFront.append(temp)
    def sort_indi_list(self):
        self.indi_list = sorted(self.indi_list, key = lambda x: x.rank)
    
    def insertIndi(self, individual):
        self.indi_list.append(individual)
        