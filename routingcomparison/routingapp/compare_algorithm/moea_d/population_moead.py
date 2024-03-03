from routingapp.compare_algorithm.moea_d.individual_moead import Individual
import numpy as np
import sys

import random

def init_weights_vectors_3d(pop_size):
    wvs = []
    for i in np.arange(0, 1 + sys.float_info.epsilon, 1 / (pop_size - 1)):
        for j in np.arange(0, 1 + sys.float_info.epsilon, 1 / (pop_size - 1)):
            if i + j <= 1:
                wvs.append([i, j, 1 - i - j])
    return np.array(wvs)

class Population:
    def __init__(self, neighborhood_size,  pop_size):
        self.pop_size = pop_size
        self.indi_list = []
        self.neighborhood_size = neighborhood_size
        self.external_pop = []
        self.weights = init_weights_vectors_3d(self.pop_size)
        self.neighborhoods = self.init_neighborhood()

    
    def init_neighborhood(self):
        B = np.empty([self.pop_size, self.neighborhood_size], dtype=int)
        for i in range(self.pop_size):
            wv = self.weights[i]
            euclidean_distances = np.empty([self.pop_size], dtype = float)
            for j in range(self.pop_size):
                euclidean_distances[j] = np.linalg.norm(wv - self.weights[j])
            B[i] = np.argsort(euclidean_distances)[:self.neighborhood_size]
        return B

    # k request
    def generate_population(self, graph, function, number_indi, k, pair_list ):
        for i in range(0, number_indi):
            indi = Individual()
            indi.generateRandom(k, pair_list, function, graph.adj_matrix, graph.predict_delay, graph.predict_bandwidth, graph.predict_loss)
            self.indi_list.append((indi))
    
    def reproduction(self, function, delay_predict_matrix, loss_predict_matrix, band_width_predict_matrix):
        O = []
        for i in range(self.pop_size):
            i1, i2 = random.sample(self.neighborhoods[i].tolist(), 2)
            off1, off2 = self.pair_reproduction(function, self.indi_list[i1], self.indi_list[i2], 
                                                delay_predict_matrix, loss_predict_matrix, 
                                                band_width_predict_matrix)
            O.append(off1)
        return O

        
    def pair_reproduction(self, function, indi1, indi2, delay_predict_matrix, 
                          loss_predict_matrix, band_width_predict_matrix):
        off1 = Individual()
        off2 = Individual()
        delay_mean1, loss_mean1, bandwidth_mean1 = 0,0,0
        delay_mean2, loss_mean2, bandwidth_mean2 = 0,0,0
        k = len(indi1.chromosome)
        for path1, path2 in zip(indi1.chromosome, indi2.chromosome):
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
    

    def natural_selection(self):
        self.indi_list, O = self.indi_list[:self.pop_size], self.indi_list[self.pop_size:]
        for i in range(self.pop_size):
            indi = O[i]
            wv  = self.weights[i]
            value_indi = np.sum(wv * indi.objectives)
            for j in self.neighborhoods[i]:
                if value_indi < np.sum(wv * self.indi_list[j].objectives):
                    self.indi_list[j] = indi
    

    def calculate_crowding_distance(self, front):
        if len(front) > 0:
            solutions_num = len(front)
            for individual in front:
                individual.crowding_distance = 0
            
            for m in range(len(front[0].objectives)):
                front = sorted(front, key = lambda x: x.objectives[m])
                front[0].crowding_distance = float('inf')
                front[solutions_num-1].crowding_distance = float('inf')
                m_values = [individual.objectives[m] for individual in front]
                scale = max(m_values) - min(m_values)
                if scale == 0:
                    scale = 1
                for i in range(1, solutions_num-1):
                    front[i].crowding_distance += (front[i+1].objectives[m] - front[i-1].objectives[m])/scale

    def update_external(self, indivs: list):
        for indi in indivs:
            old_size = len(self.external_pop)
            self.external_pop = [other for other in self.external_pop
                                 if not indi.dominates(other)]
            if old_size > len(self.external_pop):
                self.external_pop.append(indi)
                continue

            for other in self.external_pop:
                if other.dominates(indi):
                    break
            else:
                self.external_pop.append(indi)
        
        self.calculate_crowding_distance(self.external_pop)
        self.external_pop = sorted(self.external_pop, key = lambda x: x.crowding_distance, reverse = True)
        self.external_pop = self.external_pop[:self.pop_size]
    