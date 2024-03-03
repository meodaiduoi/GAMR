import numpy as np
import time
import random

from routingapp.compare_algorithm.age.individual_age import Individual

class Population:
    def __init__(self, pop_size):
        self.indi_list = []
        self.ParetoFront = []
        self.pop_size = pop_size
    # k request
    def generate_population(self, graph, function, number_indi, k, pair_list ):
        for i in range(0, number_indi):
            indi = Individual()
            indi.generateRandom(k, pair_list, function, graph.adj_matrix, graph.predict_delay, graph.predict_bandwidth, graph.predict_loss)
            self.indi_list.append((indi))
        
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
    

    def normalize_objectives_get_geometry(self):
        objectives = [individual.objectives for individual in self.ParetoFront[0]]
        objectives = list(zip(*objectives))
        max_obj = [max(obj) for obj in objectives]
        min_obj = [min(obj) for obj in objectives]
        for individual in self.indi_list:
            # individual.objectives_scale = [(obj - min_obj[i])/(max_obj[i] - min_obj[i]) for i, obj in enumerate(individual.objectives)] 
            individual.objectives_scale = []
            for i, obj in enumerate(individual.objectives):
                if max_obj[i] - min_obj[i] == 0:
                    individual.objectives_scale.append(0)
                else:
                    individual.objectives_scale.append((obj - min_obj[i])/(max_obj[i] - min_obj[i]))
        # get geometry of front
    
    def survival_score(self, front):
        for indi in front:
            proximity = np.linalg.norm(indi.objectives_scale)
            num = 0
            for other_indi in front:
                if other_indi != indi:
                    num = num + 1
            
            if num == 0:
                diversity = 0
            else:
                diversity = min([np.linalg.norm(np.array(indi.objectives_scale) - np.array(other_indi.objectives_scale)) for other_indi in front if other_indi != indi])
            indi.survival_score = diversity/proximity

    def natural_selection(self):
        self.fast_nondominated_sort()
        self.normalize_objectives_get_geometry()
        new_indivs = []
        new_fronts = []
        front_num = 0
        while len(new_indivs) + len(self.ParetoFront[front_num]) <= self.pop_size:
            new_indivs.extend(self.ParetoFront[front_num])
            new_fronts.append(self.ParetoFront[front_num])
            front_num += 1
        if len(new_indivs) < self.pop_size:
            front = self.ParetoFront[front_num]
            self.survival_score(front)
            front = sorted(front, key = lambda x: x.survival_score, reverse = True)
            new_indivs.extend(front[:self.pop_size - len(new_indivs)])
            new_fronts.append(front[:self.pop_size - len(new_indivs)])
        self.indi_list = new_indivs
                


    def sort_indi_list(self):
        self.indi_list = sorted(self.indi_list, key = lambda x: x.rank)
    
    def insertIndi(self, individual):
        self.indi_list.append(individual)
        