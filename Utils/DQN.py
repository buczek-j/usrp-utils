#!/usr/bin/env python3

'''
Deep-Q Network for USRP Drone Node

'''

import os
import sys
import numpy as np
#import tensorflow as tf
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

# a version of HiddenLayer that keeps track of params
class HiddenLayer:
  def __init__(self, M1, M2, f= tf.nn.relu, use_bias=True):
    self.W = tf.Variable(tf.random.normal(shape=(M1, M2)))
    self.params = [self.W]
    self.use_bias = use_bias
    if use_bias:
      self.b = tf.Variable(np.zeros(M2).astype(np.float32))
      self.params.append(self.b)
    self.f = f

  def forward(self, X):
    if self.use_bias:
      a = tf.matmul(X, self.W) + self.b
    else:
      a = tf.matmul(X, self.W)
    return self.f(a)


class DQN:
  def __init__(self, dqn_config):
    self.K = dqn_config.action_dim
    D = dqn_config.state_dim
    # create the graph
    self.layers = []
    M1 = D
    hidden_layer_sizes = dqn_config.hidden_layer_sizes
    for M2 in hidden_layer_sizes:
      layer = HiddenLayer(M1, M2)
      self.layers.append(layer)
      M1 = M2

    # final layer
    layer = HiddenLayer(M1, self.K, lambda x: x)
    self.layers.append(layer)

    # collect params for copy
    self.params = []
    for layer in self.layers:
      self.params += layer.params

    # inputs and targets
    self.X = tf.placeholder(tf.float32, shape=(None, D), name='X')
    self.G = tf.placeholder(tf.float32, shape=(None,), name='G')
    self.actions = tf.placeholder(tf.int32, shape=(None,), name='actions')

    # calculate output and cost
    Z = self.X
    for layer in self.layers:
      Z = layer.forward(Z)
    Y_hat = Z
    self.predict_op = Y_hat

    selected_action_values = tf.reduce_sum(
      Y_hat * tf.one_hot(self.actions, self.K),
      reduction_indices=[1]
    )

    cost = tf.reduce_sum(tf.square(self.G - selected_action_values))
    self.train_op = tf.train.AdamOptimizer(dqn_config.lr).minimize(cost)
    # self.train_op = tf.train.AdagradOptimizer(1e-2).minimize(cost)
    # self.train_op = tf.train.MomentumOptimizer(1e-3, momentum=0.9).minimize(cost)
    # self.train_op = tf.train.GradientDescentOptimizer(1e-4).minimize(cost)

    self.doubleDQN = dqn_config.doubleDQN

    # create replay memory
    self.experience = {'s': [], 'a': [], 'r': [], 's2': [], 'done': []}
    self.max_experiences = dqn_config.max_experiences
    self.min_experiences = dqn_config.min_experiences
    self.batch_sz = dqn_config.batch_sz
    self.gamma = dqn_config.gamma

  def set_session(self, session):
    self.session = session

  def copy_from(self, other):
    # collect all the ops
    ops = []
    my_params = self.params
    other_params = other.params
    for p, q in zip(my_params, other_params):
      actual = self.session.run(q)
      op = p.assign(actual)
      ops.append(op)
    # now run them all
    self.session.run(ops)

  def predict(self, X):
    X = np.atleast_2d(X)
    return self.session.run(self.predict_op, feed_dict={self.X: X})

  def train(self, target_network):
    # sample a random batch from buffer, do an iteration of GD
    if len(self.experience['s']) < self.min_experiences:
      # don't do anything if we don't have enough experience
      return

    # randomly select a batch
    idx = np.random.choice(len(self.experience['s']), size=self.batch_sz, replace=False)
    # print("idx:", idx)
    states = [self.experience['s'][i] for i in idx]
    actions = [self.experience['a'][i] for i in idx]
    rewards = [self.experience['r'][i] for i in idx]
    next_states = [self.experience['s2'][i] for i in idx]
    dones = [self.experience['done'][i] for i in idx]
    if self.doubleDQN == True:
      action_values = self.predict(next_states)
      online_action = np.argmax(action_values, axis=1)
      target_Q = target_network.predict(next_states)
      next_Q = target_Q[np.arange(len(target_Q)), online_action]
      # print("action_values:{}, online_action:{}, next_Q:{}".format(action_values, online_action, next_Q))
    else:
      next_Q = np.max(target_network.predict(next_states), axis=1)
    targets = [r + self.gamma*next_q if not done else r for r, next_q, done in zip(rewards, next_Q, dones)]

    # call optimizer
    self.session.run(
      self.train_op,
      feed_dict={
        self.X: states,
        self.G: targets,
        self.actions: actions
      }
    )

  def add_experience(self, s, a, r, s2, done):
    if len(self.experience['s']) >= self.max_experiences:
      self.experience['s'].pop(0)
      self.experience['a'].pop(0)
      self.experience['r'].pop(0)
      self.experience['s2'].pop(0)
      self.experience['done'].pop(0)
    self.experience['s'].append(s)
    self.experience['a'].append(a)
    self.experience['r'].append(r)
    self.experience['s2'].append(s2)
    self.experience['done'].append(done)

  def sample_action(self, x, eps):
    if np.random.random() < eps:
      return np.random.choice(self.K)
    else:
      X = np.atleast_2d(x)
      return np.argmax(self.predict(X)[0])

"""
class DQN:
    def __init__(self, dqn_config):
        '''
        '''
    def run(self, states):
        '''
        :param states: array of the states
        :return action: [movement action, tx action]

        '''
        return [0,0]
"""

class DQN_Config:
    def __init__(self):
        '''
        DQN configuration storage object to simplify the initialization
        '''
        self.state_dim = 6#12
        self.action_dim = 5#15
        self.hidden_layer_sizes = [50, 50]
        self.gamma = 0.99
        self.max_experiences = 10000
        self.min_experiences = 1000
        self.batch_sz = 528
        self.lr = 1e-3
        self.doubleDQN = True

def main():

    config = DQN_Config()

    config.state_dim = 6
    config.action_dim = 5
    model_restore_path = "../saved_models/asym_scenarios_50container_loc/"
    model_stage = 270
    model_path = str(model_restore_path + "tf_model_{}-{}").format("rly11", model_stage)
    state = [0, 9, 15, 6, 5, 5]

    ############
    # for loc & txp,  we use this config
    ############
    # config.state_dim = 12
    # config.action_dim = 15
    # model_restore_path = "../saved_models/asym_loc_fulltxp/"
    # model_stage = 300
    # model_path = str(model_restore_path + "tf_model_{}-{}").format("rly11", model_stage)
    # state = [0, 9, 15, 6, 5, 5, 4, 4, 4, 4, 4, 4]


    nn = DQN(config)

    init = tf.global_variables_initializer()
    session = tf.InteractiveSession()
    session.run(init)
    saver = tf.train.Saver(max_to_keep=10)

    nn.set_session(session)
    saver.restore(nn.session, model_path)

    eps = 0
    action = nn.sample_action(state, eps)

    action_list = [action % 5, action // 5]# [loc_action, txp_action]
    print("Generated action :", action_list)

if __name__ == '__main__':
    main()