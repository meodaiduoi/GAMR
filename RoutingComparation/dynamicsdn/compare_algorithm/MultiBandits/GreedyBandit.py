import random
import numpy as np
from MultiBandits.MultiBanditBase import MultiArmBandit


class Greedy(MultiArmBandit):
    def __init__(self, arms, arms_data, epsilon):
        MultiArmBandit.__init__(self, arms, arms_data)
        self.epsilon = epsilon

    def choose_arm(self):
        if random.random() > self.epsilon:
            arm = np.argmax(self.Q_values)
            return arm
        else:
            arm = random.randrange(self.arms)
            return arm
