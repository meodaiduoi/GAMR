class Individual:
    #pairs_list has k pairs (src_node, dst_node)
    #Generate random
    def __init__(self):
        self.chromosome = []
        self.routing_objectives = []
        self.objectives = []
        self.domination_count = None
        self.dominated_solutions = None
        self.rank = 0
        self.objectives_scale = []
        self.survival_score = None
    def generateRandom(self, k, pairs_list, function, adj_matrix, delay_predict_matrix, band_width_predict_matrix, loss_predict_matrix):
        delay_mean = 0
        loss_mean = 0
        bandwidth_mean = 0
        for pair in pairs_list:
            src_node = pair[0]
            dst_node = pair[1]
            new_path = function.createRandom(src_node, dst_node, adj_matrix)
            self.chromosome.append(new_path)
            predict_delay = function.cal_delay(new_path[2], delay_predict_matrix)
            predict_bandwidth = function.cal_bandwidth(new_path[2], band_width_predict_matrix)
            predict_lossPacket = function.cal_packetLoss(new_path[2], loss_predict_matrix)
            delay_mean = delay_mean + predict_delay
            loss_mean = loss_mean + predict_lossPacket
            bandwidth_mean = bandwidth_mean + predict_bandwidth
            self.routing_objectives.append((predict_delay, predict_bandwidth, predict_lossPacket))
        delay_mean = delay_mean/k
        loss_mean = loss_mean/k
        #maximize bandwidth => minimize - bandwidth
        bandwidth_mean = - bandwidth_mean/k
        self.objectives.extend([delay_mean, bandwidth_mean, loss_mean])               
                
    # Two same individuals
    def __eq__(self, other):
        if isinstance(self, other.__class__):
            return self.chromosome == other.chromosome
        return False
    #Generate Individual by mutating
    def generate_mutating(self, other_indi,function, adj_matrix,delay_predict_matrix, band_width_predict_matrix, loss_predict_matrix):
        delay_mean = 0
        loss_mean = 0
        bandwidth_mean = 0
        for path in other_indi.chromosome:
            new_path = function.createPath_insert(path[2], adj_matrix)
            self.chromosome.append((path[0],path[1],new_path))
            predict_delay = function.cal_delay(new_path, delay_predict_matrix)
            predict_bandwidth = function.cal_bandwidth(new_path, band_width_predict_matrix)
            predict_lossPacket = function.cal_packetLoss(new_path, loss_predict_matrix)
            delay_mean = delay_mean + predict_delay
            loss_mean = loss_mean + predict_lossPacket
            bandwidth_mean = bandwidth_mean + predict_bandwidth
            self.routing_objectives.append((predict_delay, predict_bandwidth, predict_lossPacket))
        
        delay_mean = delay_mean/len(other_indi.chromosome)
        loss_mean = loss_mean/len(other_indi.chromosome)
        #maximize bandwidth => minimize - bandwidth
        bandwidth_mean = - bandwidth_mean/len(other_indi.chromosome)
        self.objectives.extend([delay_mean, bandwidth_mean, loss_mean])
        
    #Check indi1 dominates indi2
    def dominates(self, other_individual):
        and_condition = True
        or_condition = False
        for first, second in zip(self.objectives, other_individual.objectives):
            and_condition = and_condition and first <= second
            or_condition = or_condition or first < second
        return (and_condition and or_condition)  
            
            
            