# coding: utf-8

import numpy as np
from chainer import cuda


class Experience:
    def __init__(self, use_gpu=0, data_size=10**5, replay_size=32, hist_size=1, initial_exploration=10**3, dim=10240):

        self.use_gpu = use_gpu
        self.data_size = data_size
        self.replay_size = replay_size
        self.preplay_size = replay_size
        self.hist_size = hist_size
        # self.initial_exploration = 10
        self.initial_exploration = initial_exploration
        self.dim = dim

        self.d = [np.zeros((self.data_size, self.hist_size, self.dim), dtype=np.uint8),
                  np.zeros(self.data_size, dtype=np.uint8),
                  np.zeros((self.data_size, 1), dtype=np.int8),
                  np.zeros((self.data_size, self.hist_size, self.dim), dtype=np.uint8),
                  np.zeros((self.data_size, 1), dtype=np.bool),
                  np.zeros((self.data_size, self.hist_size, self.dim), dtype=np.uint8),
                  np.zeros(self.data_size, dtype=np.uint8)]

    def stock(self, time, state, action, reward, state_dash, episode_end_flag, next_state_dash=[], next_action=0):
        data_index = time % self.data_size

        if episode_end_flag is True:
            self.d[0][data_index] = state
            self.d[1][data_index] = action
            self.d[2][data_index] = reward
        else:
            self.d[0][data_index] = state
            self.d[1][data_index] = action
            self.d[2][data_index] = reward
            self.d[3][data_index] = state_dash
        self.d[4][data_index] = episode_end_flag
        self.d[5][data_index] = next_state_dash
        self.d[6][data_index] = next_action

    def stock_end(self, time, state, action, reward, state_dash, episode_end_flag):
        data_index = time % self.data_size

        if episode_end_flag is True:
            self.d[0][data_index] = state
            self.d[1][data_index] = action
            self.d[2][data_index] = reward
        else:
            self.d[0][data_index] = state
            self.d[1][data_index] = action
            self.d[2][data_index] = reward
            self.d[3][data_index] = state_dash
        self.d[4][data_index] = episode_end_flag


    def replay(self, time):
        replay_start = False
        if self.initial_exploration < time:
            replay_start = True
            # Pick up replay_size number of samples from the Data
            if time < self.data_size:  # during the first sweep of the History Data
                replay_index = np.random.randint(0, time, (self.replay_size, 1))
            else:
                replay_index = np.random.randint(0, self.data_size, (self.replay_size, 1))

            s_replay = np.ndarray(shape=(self.replay_size, self.hist_size, self.dim), dtype=np.float32)
            a_replay = np.ndarray(shape=(self.replay_size, 1), dtype=np.uint8)
            r_replay = np.ndarray(shape=(self.replay_size, 1), dtype=np.float32)
            s_dash_replay = np.ndarray(shape=(self.replay_size, self.hist_size, self.dim), dtype=np.float32)
            episode_end_replay = np.ndarray(shape=(self.replay_size, 1), dtype=np.bool)
            for i in xrange(self.replay_size):
                s_replay[i] = np.asarray(self.d[0][replay_index[i]], dtype=np.float32)
                a_replay[i] = self.d[1][replay_index[i]]
                r_replay[i] = self.d[2][replay_index[i]]
                s_dash_replay[i] = np.array(self.d[3][replay_index[i]], dtype=np.float32)
                episode_end_replay[i] = self.d[4][replay_index[i]]

            if self.use_gpu >= 0:
                s_replay = cuda.to_gpu(s_replay)
                s_dash_replay = cuda.to_gpu(s_dash_replay)

            return replay_start, s_replay, a_replay, r_replay, s_dash_replay, episode_end_replay

        else:
            return replay_start, 0, 0, 0, 0, False

    def preplay(self, time):
        preplay_start = False
        if self.initial_exploration < time:
            preplay_start = True
            # Pick up replay_size number of samples from the Data
            if time < self.data_size:  # during the first sweep of the History Data
                preplay_index = np.random.randint(0, time, (self.preplay_size, 1))
            else:
                preplay_index = np.random.randint(0, self.data_size, (self.preplay_size, 1))

            s_preplay = np.ndarray(shape=(self.preplay_size, self.hist_size, self.dim), dtype=np.float32)
            a_preplay = np.ndarray(shape=(self.preplay_size, 1), dtype=np.uint8)
            r_preplay = np.ndarray(shape=(self.preplay_size, 1), dtype=np.float32)
            s_dash_preplay = np.ndarray(shape=(self.preplay_size, self.hist_size, self.dim), dtype=np.float32)
            episode_end_preplay = np.ndarray(shape=(self.preplay_size, 1), dtype=np.bool)
            for i in xrange(self.preplay_size):
                s_preplay[i] = np.asarray(self.d[3][preplay_index[i]], dtype=np.float32)
                a_preplay[i] = self.d[6][preplay_index[i]]
                r_preplay[i] = self.d[2][preplay_index[i]]
                s_dash_preplay[i] = np.array(self.d[5][preplay_index[i]], dtype=np.float32)
                episode_end_preplay[i] = self.d[4][preplay_index[i]]

            if self.use_gpu >= 0:
                s_preplay = cuda.to_gpu(s_preplay)
                s_dash_preplay = cuda.to_gpu(s_dash_preplay)

            return preplay_start, s_preplay, a_preplay, r_preplay, s_dash_preplay, episode_end_preplay

        else:
            return preplay_start, 0, 0, 0, 0, False


    def end_episode(self, time, last_state, action, reward):
        self.stock_end(time, last_state, action, reward, last_state, True)
        replay_start, s_replay, a_replay, r_replay, s_dash_replay, episode_end_replay = \
            self.replay(time)

        return replay_start, s_replay, a_replay, r_replay, s_dash_replay, episode_end_replay
