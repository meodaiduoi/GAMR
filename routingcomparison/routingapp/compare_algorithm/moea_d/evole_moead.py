from routingapp.compare_algorithm.moea_d.individual_moead import *
import random

class Evolutionary:
    def __init__(self):
        #solution includes last solution after n generations
        #solution include solution_space after n generations
        self.solution = None
        self.solution_space = None
    
    def evolve(self, population, function, graph, number_generation, number_indi, pm, pc, number_particips, number_stop):
        population.update_external(population.indi_list)
        for i in range(number_generation):
            offspring = population.reproduction(function, graph.predict_delay, graph.predict_loss, 
                                                graph.predict_bandwidth)
            population.update_external(offspring)
            population.indi_list.extend(offspring)
            population.natural_selection()
        
        return population.external_pop

    # def evolve1(self, population, function, graph, number_generation, number_indi, pm, number_stop):
    #     self.solution = None
    #     self.solution_space =[]
    #     temp_solution = None
    #     count_time = 0
    #     #mutated
    #     for i in range(number_generation):
    #         off_list = []
    #         for indi in population.indi_list:
    #             if random.random() < pm:
    #                 new_indi = Individual()
    #                 new_indi.generate_mutating(indi, function, graph.adj_matrix, graph.predict_delay, graph.predict_bandwidth, graph.predict_loss)
    #                 off_list.append(new_indi)
    #         population.indi_list.extend(off_list)
    #         population.fast_nondominated_sort()
    #         population.sort_indi_list()
    #         del population.indi_list[number_indi:]
            

    #         if function.select_solution(population.ParetoFront[0]) == temp_solution:
    #             count_time = count_time + 1
    #             if count_time == number_stop:
    #                 break
    #         else:
    #             temp_solution = function.select_solution(population.ParetoFront[0])
    #     self.solution = population.ParetoFront[0]
    #     return self.solution
            