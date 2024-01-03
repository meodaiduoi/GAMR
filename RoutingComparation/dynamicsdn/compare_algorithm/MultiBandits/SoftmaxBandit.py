import numpy as np
from MultiBandits.MultiBanditBase import MultiArmBandit


class Softmax(MultiArmBandit):
    def __init__(self, arms, arms_data, temperature):
        MultiArmBandit.__init__(self, arms, arms_data)
        self.temperature = temperature

    def choose_arm(self):
        probs = np.zeros(self.arms)
        exp_values = np.zeros(self.arms)
        for arm in range(self.arms):
            exp_values[arm] = np.exp(self.Q_values[arm] / self.temperature)
        probs = exp_values / np.sum(exp_values)
        arm = np.random.choice(np.arange(self.arms), p=probs)
        return arm
