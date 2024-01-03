import numpy as np
from MultiBandits.MultiBanditBase import MultiArmBandit


class UCB(MultiArmBandit):
    def __init__(self, arms, arms_data, constant):
        MultiArmBandit.__init__(self, arms, arms_data)
        self.constant = constant
        self.first_N_rounds_UCB = [arm for arm in range(self.arms)]

    def choose_arm(self):
        if not self.first_N_rounds_UCB:
            arm = self.choose_arm_UCB()
        # N lan ban dau se chon theo round robin
        else:
            arm = self.choose_arm_Round_Robin()
        return arm

    def choose_arm_UCB(self):
        # number of previous steps
        n = sum(self.counts)
        ucb_values = np.zeros(self.arms)
        for arm in range(self.arms):
            confidence = self.constant * \
                np.sqrt(np.log(n) / float(self.counts[arm]))
            ucb_values[arm] = self.Q_values[arm] + confidence
        return np.argmax(ucb_values)

    def choose_arm_Round_Robin(self):
        return self.first_N_rounds_UCB.pop(0)
