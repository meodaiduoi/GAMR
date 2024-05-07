import gym as gym
import torch
import numpy as np
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter
import tianshou as ts
from tianshou.env import DummyVectorEnv
from torch.optim.lr_scheduler import LambdaLR
import torch.nn.functional as F
import os
from routingapp.compare_algorithm.sec_morl_multipolicy.rl import SDN_Env
from routingapp.compare_algorithm.sec_morl_multipolicy.network import conv_mlp_net

from tianshou.utils.net.discrete import Actor, Critic

expn = 'exp1'
config = 'multi-edge'
lr, epoch, batch_size = 1e-6, 1, 1024 * 4
train_num, test_num = 64, 1024
gamma, lr_decay = 0.9, None
buffer_size = 100000
eps_train, eps_test = 0.1, 0.00
step_per_epoch, episode_per_collect = 100 * train_num * 700, train_num
writer = SummaryWriter('tensor-board-log/ppo')
logger = ts.utils.TensorboardLogger(writer)
is_gpu_default = torch.cuda.is_available()

gae_lambda, max_grad_norm = 0.95, 0.5
vf_coef, ent_coef = 0.5, 0.0
rew_norm, action_scaling = False, False
bound_action_method = "clip"
eps_clip, value_clip = 0.2, False
repeat_per_collect = 2
dual_clip, norm_adv = None, 0.0
recompute_adv = 0

INPUT_CH = 67
FEATURE_CH = 512
MLP_CH = 1024


class sdn_net(nn.Module):
    def __init__(self, edge_num, cloud_num, mode='actor', is_gpu=is_gpu_default):
        super().__init__()
        self.is_gpu = is_gpu
        self.mode = mode
        self.edge_num = edge_num
        self.cloud_num = cloud_num
        if self.mode == 'actor':
            self.network = conv_mlp_net(conv_in=INPUT_CH, conv_ch=FEATURE_CH, mlp_in=(self.edge_num+self.cloud_num)*FEATURE_CH,\
                                    mlp_ch=MLP_CH, out_ch=self.edge_num+self.cloud_num, block_num=3)
        else:
            self.network = conv_mlp_net(conv_in=INPUT_CH, conv_ch=FEATURE_CH, mlp_in=(self.edge_num+self.cloud_num)*FEATURE_CH,\
                                    mlp_ch=MLP_CH, out_ch=self.edge_num, block_num=3)
        
    def load_model(self, filename):
        map_location=lambda storage, loc:storage
        self.load_state_dict(torch.load(filename, map_location=map_location))
        print('load model!')
    
    def save_model(self, filename):
        torch.save(self.state_dict(), filename)
        # print('save model!')

    def forward(self, obs, state=None, info={}):
        state = obs#['servers']
        state = torch.tensor(state).float()
        if self.is_gpu:
            state = state.cuda()

        logits = self.network(state)
        
        return logits, state

class Actor(nn.Module):
    def __init__(self, edge_num, cloud_num, is_gpu=is_gpu_default, dist_fn=None):
        super().__init__()
        self.is_gpu = is_gpu
        self.edge_num = edge_num
        self.cloud_num = cloud_num

        self.net = sdn_net(mode='actor', edge_num=self.edge_num, cloud_num=self.cloud_num)

    def load_model(self, filename):
        map_location=lambda storage, loc:storage
        self.load_state_dict(torch.load(filename, map_location=map_location))
        print('load model!')
    
    def save_model(self, filename):
        torch.save(self.state_dict(), filename)
        # print('save model!')

    def forward(self, obs, state=None, info={}):
            
        logits,_ = self.net(obs)
        # Adjust output size according to the new action space
        logits = F.sigmoid(logits)

        return logits, state

class Critic(nn.Module):
    def __init__(self, edge_num, cloud_num, is_gpu=is_gpu_default):
        # print(f"Batch keys: {self.__dict__.keys()}")
        super().__init__()

        self.is_gpu = is_gpu
        self.edge_num = edge_num
        self.cloud_num = cloud_num

        self.net = sdn_net(mode='critic', edge_num=self.edge_num, cloud_num=self.cloud_num)

    def load_model(self, filename):
        map_location=lambda storage, loc:storage
        self.load_state_dict(torch.load(filename, map_location=map_location))
        print('load model!')
    
    def save_model(self, filename):
        torch.save(self.state_dict(), filename)
        # print('save model!')

    def forward(self, obs, state=None, info={}):
            
        v,_ = self.net(obs)

        return v

def train_sdn_policy(graph, request):
    
    actor = Actor(is_gpu=is_gpu_default, edge_num = graph.number_edge_servers, cloud_num = graph.number_cloud_servers)
    critic = Critic(is_gpu=is_gpu_default, edge_num = graph.number_edge_servers, cloud_num = graph.number_cloud_servers)
    actor_critic = ts.utils.net.common.ActorCritic(actor, critic)
    optim = torch.optim.Adam(actor_critic.parameters(), lr=lr)

    dist = torch.distributions.Bernoulli

    # Define action space using gym.spaces.Box
    action_space = gym.spaces.Box(low=np.zeros(graph.number_edge_servers+graph.number_cloud_servers), high=np.ones(graph.number_edge_servers+graph.number_cloud_servers), shape=(graph.number_edge_servers+graph.number_cloud_servers, ))
    if lr_decay:
        lr_scheduler = LambdaLR(
            optim, lr_lambda=lambda epoch: lr_decay ** (epoch - 1)
        )
    else:
        lr_scheduler = None
    policy = ts.policy.PPOPolicy(actor, critic, optim, dist,
            discount_factor=gamma, max_grad_norm=max_grad_norm,
            eps_clip=eps_clip, vf_coef=vf_coef,
            ent_coef=ent_coef, reward_normalization=rew_norm,
            advantage_normalization=norm_adv, recompute_advantage=recompute_adv,
            dual_clip=dual_clip, value_clip=value_clip,
            gae_lambda=gae_lambda, action_space=action_space,
            lr_scheduler=lr_scheduler,
        )
    for i in range(101):
        try:
            os.mkdir('save/pth-e%d/' % (graph.number_edge_servers) + 'cloud%d/' % (graph.number_cloud_servers) + expn + '/w%03d' % (i))
        except:
            pass


    for wi in range(100, 0 - 1, -2):

        if wi == 100:
            epoch_a = epoch * 10
        else:
            epoch_a = epoch

        train_envs = DummyVectorEnv(
            [lambda: SDN_Env(graph = graph, conf_name=config, request=request, w=wi / 100.0) for _ in range(train_num)])
        test_envs = DummyVectorEnv(
            [lambda: SDN_Env(graph = graph, conf_name=config, request=request, w=wi / 100.0) for _ in range(test_num)])
        buffer = ts.data.VectorReplayBuffer(buffer_size, train_num)
        train_collector = ts.data.Collector(
            policy=policy,
            env=train_envs,
            buffer=buffer,
        )
        # print(train_collector.env.action_space)
        test_collector = ts.data.Collector(policy, test_envs)
        train_collector.collect(n_episode=train_num)

        def save_best_fn(policy, epoch, env_step, gradient_step):
            pass

        def test_fn(epoch, env_step):
            policy.actor.save_model('save/pth-e%d/' % (graph.number_edge_servers) + 'cloud%d/' % (graph.number_cloud_servers) + expn + '/w%03d/ep%02d-actor.pth' % (wi, epoch))
            policy.critic.save_model('save/pth-e%d/' % (graph.number_edge_servers) + 'cloud%d/' % (graph.number_cloud_servers) + expn + '/w%03d/ep%02d-critic.pth' % (wi, epoch))

        def train_fn(epoch, env_step):
            pass

        def reward_metric(rews):
            return rews

        result = ts.trainer.onpolicy_trainer(
            policy=policy,
            train_collector=train_collector,
            test_collector=test_collector,
            max_epoch=epoch_a,
            step_per_epoch=step_per_epoch,
            repeat_per_collect=repeat_per_collect,
            episode_per_test=test_num,
            batch_size=batch_size,
            step_per_collect=None,
            episode_per_collect=episode_per_collect,
            train_fn=train_fn,
            test_fn=test_fn,
            save_best_fn=save_best_fn(policy, epoch, 0, 0),
            stop_fn=None,
            save_checkpoint_fn=save_best_fn(policy, epoch, 0, 0),
            reward_metric=reward_metric,
            logger=logger,
        )
    return result 
 