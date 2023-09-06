import numpy as np
from random import normalvariate

def normdist_param(mean, std_dev, round=2):
    '''
        Generating normal dist link 
        param for mininet
    '''
    return round(np.random.normal(mean, std_dev))

# Normal choice
# https://stackoverflow.com/questions/35472461/select-one-element-from-a-list-using-python-following-the-normal-distribution
def normdist_array_genparam(numbers, mean=None, stddev=None):
    if mean is None:
        # if mean is not specified, use center of list
        mean = (len(numbers) - 1) / 2

    if stddev is None:
        # if stddev is not specified, let list be -3 .. +3 standard deviations
        stddev = len(numbers) / 6

    while True:
        index = int(normalvariate(mean, stddev) + 0.5)
        if 0 <= index < len(numbers):
            return numbers[index]

def gen_loss():
    return np.random.choice(
                        [0, 1, 2, 4, 5, 7],
                        p=[0.37, 0.23, 0.15, 0.12, 0.08, 0.05]
                    )