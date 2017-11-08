import os
import sys
import tensorflow as tf
import pandas as pd
import numpy as np
import time
from collections import namedtuple

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
print("Python version " + sys.version)
print("Tensorflow version " + tf.__version__)


def fc_layer(input, dim_in, dim_out, name='fc_layer'):

    with tf.name_scope(name):
        W = tf.Variable(tf.truncated_normal([dim_in, dim_out], stddev=2.0/dim_in), name='W')
        B = tf.Variable(tf.zeros([dim_out]), name='B')
        nonlinearity = tf.nn.relu(tf.matmul(input, W) + B)
        tf.summary.histogram("weights", W)
        tf.summary.histogram("biases", B)
        tf.summary.histogram("nonlinearity", nonlinearity)
        return nonlinearity


def rank1_ff_nn(nb_features, nn_layer_sizes, nb_labels):

    nn = namedtuple('nn', ['inputs', 'labels', 'pred', 'loss'])

    tf.reset_default_graph()

    # Placeholders for labeled pair of training data.
    nn.inputs = tf.placeholder(tf.float32, [None, nb_features], name='inputs')
    nn.labels = tf.placeholder(tf.float32, [None, nb_labels], name='labels')

    # Build the computational graph consisting of a feed forward NN. 
    nb_hidden_layers = len(nn_layer_sizes)

    layers = []

    layers.append(fc_layer(nn.inputs, nb_features, nn_layer_sizes[0], 'fc_hidden0'))

    for i in range(nb_hidden_layers - 1):

        layers.append(fc_layer(layers[i], nn_layer_sizes[i], 
                      nn_layer_sizes[i+1], 'fc_hidden%s' % str(i+1)))

    nn.pred = fc_layer(layers[-1], nn_layer_sizes[-1], nb_labels, 'pred')

    layers.append(nn.pred)

    # Define the loss function.
    with tf.name_scope('loss'):
        nn.loss = tf.reduce_sum(tf.square(nn.pred-nn.labels))
        tf.summary.scalar('loss', nn.loss)

    # Define accuracy to be % of predictions within certain delta of labels.
    with tf.name_scope('accuracy'):

        # Accuracy to 1E-3
        close_prediction_3dp = tf.less_equal(tf.abs(nn.pred-nn.labels), 1E-3)
        nn.acc_3dp = tf.reduce_mean(tf.cast(close_prediction_3dp, tf.float32))
        tf.summary.scalar('accuracy_3dp', nn.acc_3dp)

        # Accuracy to 1E-4
        close_prediction_4dp = tf.less_equal(tf.abs(nn.pred-nn.labels), 1E-4)
        nn.acc_4dp = tf.reduce_mean(tf.cast(close_prediction_4dp, tf.float32))
        tf.summary.scalar('accuracy_4dp', nn.acc_4dp)

        # Accuracy to 1E-5
        close_prediction_5dp = tf.less_equal(tf.abs(nn.pred-nn.labels), 1E-5)
        nn.acc_5dp = tf.reduce_mean(tf.cast(close_prediction_5dp, tf.float32))
        tf.summary.scalar('accuracy_5dp', nn.acc_5dp)

    return nn



if __name__ == '__main__':

    CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

    # Configuration.
    ID = 4
    train_config = ['lab_data_3_1/train_uniform.csv', [0, 1, 2], [3]]
    valid_config = ['lab_data_3_1/validation_uniform.csv', [0, 1, 2], [3]]
    test_config = ['lab_data_3_1/test_uniform.csv', [0, 1, 2], [3]]
    mini_batch_size = 100
    nn_layer_sizes = [64, 32]
    lr = 0.00001
    seed = 1
    nb_epochs = 10**4

    LOGDIR = "run%s/" % str(ID)
    model_path = './run%s/checkpoints/' % str(ID)

    train(train_config, valid_config, mini_batch_size, nn_layer_sizes, lr, seed, nb_epochs)

    # test_acc(test_config, nn_layer_sizes, model_path)

    # time_benchmark(test_config, nn_layer_sizes, model_path)

