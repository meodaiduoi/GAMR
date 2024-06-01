#!/usr/bin/env python
# coding: utf-8

import gymnasium as gym, torch, numpy as np, torch.nn as nn
from torch.utils.tensorboard import SummaryWriter
from tianshou.env import DummyVectorEnv
import torch.nn.functional as F

class mlp_resblock(nn.Module):
    def __init__(self, in_ch, ch, out_ch=None, block_num=3, is_in=False):
        super().__init__()
        self.models=nn.Sequential()
        self.relus=nn.Sequential()
        self.block_num = block_num
        self.is_in = is_in
        self.is_out = out_ch
        
        if self.is_in:
            self.in_mlp = nn.Sequential(*[
                nn.Linear(in_ch, ch), 
                nn.GELU('tanh')])
        for i in range(self.block_num):
            self.models.add_module(str(i), nn.Sequential(*[
                nn.Linear(ch, ch),
                nn.GELU('tanh'),
                nn.Linear(ch, ch)]))
            self.relus.add_module(str(i), nn.Sequential(*[
                nn.GELU('tanh')]))
        if self.is_out:
            self.out_mlp = nn.Sequential(*[
            nn.Linear(ch, ch), 
            nn.GELU('tanh'),
            nn.Linear(ch, out_ch)])
            
    def forward(self, x):
        if self.is_in:
            x = self.in_mlp(x)
        for i in range(self.block_num):
            x0 = x
            x = self.models[i](x)
            x += x0
            x = self.relus[i](x)
        if self.is_out:
            x = self.out_mlp(x)
        return x

class mlp_resblock_gelu(nn.Module):
    def __init__(self, in_ch, ch, out_ch=None, block_num=3, is_in=False, is_gelu=True):
        super().__init__()
        self.models=nn.Sequential()
        self.relus=nn.Sequential()
        self.block_num = block_num
        self.is_in = is_in
        self.is_out = out_ch
        self.is_gelu = is_gelu
        
        if self.is_in:
            self.in_mlp = nn.Sequential(*[
                nn.Linear(in_ch, ch), 
                nn.GELU('tanh')])
        for i in range(self.block_num):
            self.models.add_module(str(i), nn.Sequential(*[
                nn.Linear(ch, ch),
                nn.GELU('tanh'),
                nn.Linear(ch, ch)]))
            self.relus.add_module(str(i), nn.Sequential(*[
                nn.GELU('tanh')]))
        if self.is_out:
            self.out_mlp = nn.Sequential(*[
            nn.Linear(ch, ch), 
            nn.GELU('tanh'),
            nn.Linear(ch, out_ch)
            ])
        if self.is_gelu:
            self.gelu = nn.GELU()

    def forward(self, x):
        if self.is_in:
            x = self.in_mlp(x)
        for i in range(self.block_num):
            x0 = x
            x = self.models[i](x)
            x += x0
            x = self.relus[i](x)
        if self.is_out:
            x = self.out_mlp(x)
        if self.is_gelu:
            x = self.gelu(x)
        return x

class conv_resblock(nn.Module):
    def __init__(self, in_ch=None, ch=256, out_ch=None, block_num=3, is_gelu=True):
        super().__init__()
        self.models=nn.Sequential()
        self.relus=nn.Sequential()
        self.block_num = block_num
        self.is_in = in_ch
        self.is_out = out_ch
        self.is_gelu = is_gelu
        
        if self.is_in:
            self.in_conv = nn.Sequential(*[
            nn.Conv1d(in_ch, ch, kernel_size=1, stride=1, padding=0),
            nn.GELU('tanh')])
        for i in range(self.block_num):
            self.models.add_module(str(i), nn.Sequential(*[
                nn.Conv1d(ch, ch, kernel_size=1, stride=1, padding=0),
                nn.GELU('tanh'),
                nn.Conv1d(ch, ch, kernel_size=1, stride=1, padding=0)]))
            self.relus.add_module(str(i), nn.Sequential(*[
                nn.GELU('tanh')]))
        if self.is_out:
            self.out_conv = nn.Conv1d(ch, out_ch, kernel_size=1, stride=1, padding=0)
        if self.is_gelu:
            self.gelu = nn.GELU()

    def forward(self, x):
        if self.is_in:
            x = self.in_conv(x)
        for i in range(self.block_num):
            x0 = x
            x = self.models[i](x)
            x += x0
            x = self.relus[i](x)
        if self.is_out:
            x = self.out_conv(x)
        if self.is_gelu:
            x = self.gelu(x)
        return x

class conv_mlp_net(nn.Module):
    def __init__(self, conv_in, conv_ch, mlp_in, mlp_ch, out_ch, block_num=3, is_gpu=True):
        super().__init__()
        input_dim = 36
        action_dim = 2
        self.is_gpu = is_gpu
        # Fit the input dimension to the input of the mlp
        self.mlp_in = mlp_in 

        self.feature_network_A = conv_resblock(in_ch=conv_in, ch=conv_ch, out_ch=conv_ch, block_num=block_num)
        self.feature_network_B = mlp_resblock(in_ch=mlp_in, ch=mlp_ch, out_ch=out_ch, block_num=block_num, is_in=True)

    def load_model(self, filename):
        map_location=lambda storage, loc:storage
        self.load_state_dict(torch.load(filename, map_location=map_location))
        # print('load model!')
    
    def save_model(self, filename):
        torch.save(self.state_dict(), filename)
        # print('save model!')

    def forward(self, obs):

        x = self.feature_network_A(obs)
        # print("Shape after conv_resblock:", x.shape)

        x = x.view(-1, self.mlp_in)
        # print("Shape after view:", x.shape)
        

        x = self.feature_network_B(x)
        # print("Shape after mlp_resblock:", x.shape)
        
        return x
