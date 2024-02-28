import numpy as np

class MABBase():
    '''
        Multi-arm bandit base class
        provide foundation for other
        MAB variations
    '''
    def __init__(self, n_arms) -> None:
        '''
        
        '''
        # n_arms aka k
        self.n_arms = n_arms
        self.reset()
        

    def reset(self):
        """
        Resets the internal state of the MAB, typically used to start a new experiment.
        """
        self.counts = np.zeros(self.n_arms)  # Count of times each arm has been played
        self.values = np.zeros(self.n_arms)  # Estimated value of each arm

    def select_arm(self):
        """
        Selects an arm to play based on the algorithm's strategy.
        Must be implemented by subclasses.

        Returns:
            The index of the selected arm.
        """
        raise NotImplementedError("Subclasses must implement select_arm()")

    def update(self, chosen_arm, reward):
        """
        Updates the internal state of the MAB based on the chosen arm and received reward.

        Args:
            chosen_arm: The index of the arm that was played.
            reward: The reward received for playing the chosen arm.
        """
        self.counts[chosen_arm] += 1
        # Update estimated value using a simple average (can be modified in subclasses)
        self.values[chosen_arm] += (reward - self.values[chosen_arm]) / self.counts[chosen_arm]


class GaussianBandit(MABBase):
    ...
    
class BinomialBandit(MABBase):
    ...
