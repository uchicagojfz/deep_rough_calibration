# LEARN BLACKSCHOLES IMPLIED VOLATILITY WITH A NEURAL NETWORK
# ==============================================================================

import numpy as np
import os
import sys
import tensorflow as tf
import logging
from blackscholes import pricer as bs_pricer

os.environ['TF_CPP_MIN_LOG_LEVEL']='2'
LOGDIR = "/tmp/deep_blackscholes/run9"
tf.set_random_seed(0)

print("Python version " + sys.version)
print("Tensorflow version " + tf.__version__)

# BLACK-SCHOLES SPECIFIC STUFF
# ==============================================================================

# Parameters of Black-Scholes function (bar the volatility).
flag = 'c'
spot = 1
strike = 1
time_to_maturity = 1
risk_free_rate = 0

# Small helper function that creates batch of labeled data.
def create_batch(nb_samples, min_vol, max_vol):
    """
    Produces a synthetic sample of labeled data suitable for learning.
    """
    
    vol_samples = np.random.uniform(min_vol, max_vol, nb_samples)
    price_samples = bs_pricer(flag, spot, strike, time_to_maturity, 
                              vol_samples, risk_free_rate)

    vol_samples = vol_samples.reshape(-1,1)
    price_samples = price_samples.reshape(-1,1)
    
    return price_samples, vol_samples


# TENSORFLOW/TENSORBOARD STUFF
# ==============================================================================

def fc_layer(input, dim_in, dim_out, name='fc_layer'):
    with tf.name_scope(name):
        W = tf.Variable(tf.truncated_normal([dim_in, dim_out], stddev=0.1), name='W')
        B = tf.Variable(tf.ones([dim_out])/10, name='B')
        nonlinearity = tf.nn.relu(tf.matmul(input, W) + B)
        tf.summary.histogram("weights", W)
        tf.summary.histogram("biases", B)
        tf.summary.histogram("nonlinearity", nonlinearity)
        return nonlinearity

def deep_impliedvol_model(learning_rate, eps):

    tf.reset_default_graph()

    # Placeholders for labeled pair of training data.
    X = tf.placeholder(tf.float32, [None, 1], name='input')
    Y_ = tf.placeholder(tf.float32, [None, 1], name='labels')

    # Specify # neurons per layer and build graph.
    neurons_1 = 500
    neurons_2 = 100
    neurons_3 = 1

    fc1 = fc_layer(X, 1, neurons_1, 'fc1')
    fc2 = fc_layer(fc1, neurons_1, neurons_2, 'fc2')
    Y = fc_layer(fc2, neurons_2, 1, 'pred')

    # Define the loss function.
    with tf.name_scope('loss'):
        loss = tf.reduce_sum(tf.square(Y-Y_))
        tf.summary.scalar('loss', loss)

    # Define training step.
    with tf.name_scope('training'):
        train_step = tf.train.AdamOptimizer(learning_rate).minimize(loss)

    # Define accuracy to be percentage of predictions within eps of labels.
    with tf.name_scope('accuracy'):
        close_prediction = tf.less_equal(tf.abs(Y-Y_), eps)
        accuracy = tf.reduce_mean(tf.cast(close_prediction, tf.float32))
        tf.summary.scalar('accuracy', accuracy)

    summary = tf.summary.merge_all()

    # Initialise session.
    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    # Create writers for train and test data.
    train_writer = tf.summary.FileWriter(LOGDIR + "_train")
    train_writer.add_graph(sess.graph)
    test_writer = tf.summary.FileWriter(LOGDIR + "_test")
    test_writer.add_graph(sess.graph)

    # Create test sample.
    test_X, test_Y = create_batch(1000, 0.01, 2)

    # Run training loops.
    for i in range(10**4):

        train_X, train_Y = create_batch(100, 0.01, 2)

        if i % 10 == 0:
            train_sum = sess.run(summary, feed_dict={X: train_X, Y_: train_Y})
            train_writer.add_summary(train_sum, i)
            test_sum = sess.run(summary, feed_dict={X: test_X, Y_: test_Y})
            test_writer.add_summary(test_sum, i)

        # Run backpropagation.
        sess.run(train_step, feed_dict={X: train_X, Y_: train_Y})


def main():

    learning_rate = 0.005
    eps = 0.001

    deep_impliedvol_model(learning_rate, eps)

    print('Run `tensorboard --logdir=%s` to see the results.' % LOGDIR)

if __name__ == '__main__':
    main()

