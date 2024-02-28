def path_cost(link_utilz, pkloss_rate, delay):
    '''
        path_cost or reget cost for mab func
        path_cost = w1*link_utilz + w2*pkloss_rate + w3*delay
    '''
    w1 = 2
    w2 = 1
    w3 = 3
    return w1*link_utilz + w2*pkloss_rate + w3*delay

