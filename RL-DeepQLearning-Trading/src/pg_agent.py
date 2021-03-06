import random
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Reshape, Flatten
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import load_model
from tensorflow.keras.losses import Huber
from tensorflow.keras.metrics import RootMeanSquaredError
from src.utils import timestamp
import tensorflow as tf
import datetime

#from keras.layers.convolutional import Convolution2D


class PGAgent:
    # def __init__(self, state_size, action_size, pretrained = False, model_name = None, window_size = 10):
    def __init__(self, state_size, pretrained = False, model_name = None, window_size = 10):
        self.state_size = state_size
        self.action_size = 3
        self.gamma = 0.99
        self.learning_rate = 0.001
        self.loss = Huber
        self.optimizer = Adam(lr = self.learning_rate)
        self.states = []
        self.gradients = []
        self.rewards = []
        self.probs = []
        self.model_name = None
        self.n_iter = 1
        self.model_type = "pg"
        self.model = self._build_model()
        self.model.summary()

    def _build_model(self):

        model = Sequential()
        model.add(Dense(units=256, activation="relu", input_shape=(self.state_size,)))
        model.add(Dense(units=512, activation="relu"))
        model.add(Dense(units=512, activation="relu"))
        model.add(Dense(units=256, activation="relu"))
        model.add(Dense(units=self.action_size, activation="softmax"))

        model.compile(optimizer = self.optimizer, loss = self.loss(), metrics = [self.metrics()])
        # model = Sequential()
        # model.add(Reshape((1, 80, 80), input_shape=(self.state_size,)))
        # model.add(Convolution2D(32, 6, 6, subsample=(3, 3), border_mode='same',
        #                         activation='relu', init='he_uniform'))
        # model.add(Flatten())
        # model.add(Dense(64, activation='relu', init='he_uniform'))
        # model.add(Dense(32, activation='relu', init='he_uniform'))
        # model.add(Dense(self.action_size, activation='softmax'))
        # opt = Adam(lr=self.learning_rate)
        # model.compile(loss='categorical_crossentropy', optimizer=opt)
        return model

    def memorize(self, state, action, prob, reward):
        y = np.zeros([self.action_size])
        y[action] = 1
        self.gradients.append(np.array(y).astype('float32') - prob)
        self.states.append(state)
        self.rewards.append(reward)
        
    def action(self, state, evaluation = False):
        #state = state.reshape([1, state.shape[0]])

        # if not evaluation and (random.random() <= self.rar):
        #     return random.randrange(self.action_size)
        
        if evaluation == True:
            action_probs = self.model.predict(state)
            return np.argmax(action_probs[0]), action_probs

        aprob = self.model.predict(state, batch_size=1).flatten()
        self.probs.append(aprob)
        prob = aprob / np.sum(aprob)
        action = np.random.choice(self.action_size, 1, p=prob)[0]
        return action, prob

    def discount_rewards(self, rewards):
        discounted_rewards = np.zeros_like(rewards)
        running_add = 0
        for t in reversed(range(0, rewards.size)):
            if rewards[t] != 0:
                running_add = 0
            running_add = running_add * self.gamma + rewards[t]
            discounted_rewards[t] = running_add
        return discounted_rewards

    def train(self):
        gradients = np.vstack(self.gradients)
        rewards = np.vstack(self.rewards)
        rewards = self.discount_rewards(rewards)
        #reward = (reward - np.mean(rewards)) / (np.std(rewards) + 1e-7)
        gradients *= rewards
        X = np.squeeze(np.vstack([self.states]))
        Y = self.probs + self.learning_rate * np.squeeze(np.vstack([gradients]))
        #self.model.train_on_batch(X, Y)
        # Adding logs for tensorboard 

        #log_dir = "logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir="./logs", histogram_freq=1, write_graph=True,update_freq=1,profile_batch=0)

        loss = self.model.fit(X, Y,callbacks=[tensorboard_callback]).history["loss"][0]
        self.states, self.probs, self.gradients, self.rewards = [], [], [], []

        return loss

    def load(self):
        #self.model.load_weights(name)
        model = load_model(f"models/{self.model_name}", custom_objects = self.custom_objects, compile=False)
        model.compile(optimizer = self.optimizer, loss = self.loss(), metrics = [self.metrics()])
        return model

    def save(self, episode):
        #self.model.save_weights(name)
        if self.model_name is None:
            self.model_name = f'{self.model_type}_{timestamp()}'
            self.model.save(f"models/{self.model_name}_{episode}")

def preprocess(I):
    I = I[35:195]
    I = I[::2, ::2, 0]
    I[I == 144] = 0
    I[I == 109] = 0
    I[I != 0] = 1
    return I.astype(np.float).ravel()

# if __name__ == "__main__":
#     env = gym.make("Pong-v0")
#     state = env.reset()
#     prev_x = None
#     score = 0
#     episode = 0

#     state_size = 80 * 80
#     action_size = env.action_space.n
#     agent = PGAgent(state_size, action_size)
#     agent.load('pong.h5')
#     while True:
#         env.render()

#         cur_x = preprocess(state)
#         x = cur_x - prev_x if prev_x is not None else np.zeros(state_size)
#         prev_x = cur_x

#         action, prob = agent.action(x)
#         state, reward, done, info = env.step(action)
#         score += reward
#         agent.memorize(x, action, prob, reward)

#         if done:
#             episode += 1
#             agent.train()
#             print('Episode: %d - Score: %f.' % (episode, score))
#             score = 0
#             state = env.reset()
#             prev_x = None
#             if episode > 1 and episode % 10 == 0:
#                 agent.save('pong.h5')
