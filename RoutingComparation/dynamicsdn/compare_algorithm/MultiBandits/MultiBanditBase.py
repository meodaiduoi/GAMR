import random
import numpy as np


class MultiArmBandit:
    def __init__(self, arms, arms_data):
        """

        arms_data: dictionary nested dictionary: example:   
        {
            0: {'ip_server': "10.0.0.2", 'total_cost': 2},

            1: {'ip_server': "10.0.0.4", 'total_cost': 4}
        }

        arm is equal to index of server: index = 0 => ip server 10.0.0.2

        arms: number of servers: int values
        """
        self.arms_data = arms_data
        # number of arms
        self.arms = arms
        self.Q_values = [0.0 for i in range(self.arms)]
        # save times for selected arms
        self.counts = [0 for i in range(self.arms)]
        self.total_rewards = 0

        # current_time = int(time.time())
        # np.random.seed(current_time)
        # print("current seed:", current_time)

    def get_reward(self, arm):
        return self.arms_data[arm]['total_cost']
#         return random.randint(0, 100)

    def choose_arm(self):
        pass

    def update(self, arm, reward):
        self.counts[arm] = self.counts[arm] + 1
        # number of previous steps
        n = self.counts[arm]
        Q_value = self.Q_values[arm]
        new_Q_value = Q_value + 1/n * (reward - Q_value)
        self.Q_values[arm] = new_Q_value

    # def run(self):
    #     average_rewards_history = []

    #     for i in range(self.epochs):
    #         arm = self.choose_arm()
    #         reward = self.get_reward(arm)
    #         self.update(arm, reward)
    #         self.total_rewards +=  reward
    #         average_rewards_history.append(self.total_rewards/ (i+1))

    #     return average_rewards_history

    def get_counts(self):
        return self.counts
