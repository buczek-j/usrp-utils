#!/usr/bin/env python3

'''
Deep-Q Network for USRP Drone Node

'''

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

class DQN_Config:
    def __init__(self):
        '''
        DQN configuration storage object to simplify the initialization
        '''

def main():
    config = DQN_Config()
    nn = DQN(config)
    print(nn.run([0, 9, 15, 6, 5, 5, -1, -1, -1, -1,-1, -1]))

if __name__ == '__main__':
    main()