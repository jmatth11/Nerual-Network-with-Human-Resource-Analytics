import tensorflow as tf
import pandas as pd
import numpy as np
import sys


np.random.seed(7)
tf.set_random_seed(7)

init_data = pd.read_csv("./HR_comma_sep.csv")

# take a look at the info
# we see no rows are missing in any column. We also see "sales" and "salary" are object types.
print(init_data.info())

# lets take a look at the first 5 entries of object data
print("Sales: {0}".format(init_data["sales"][:5]))
print("Salary: {0}".format(init_data["salary"][:5]))

# We can see that sales looks like nominal data and salary looks like ordinal data
# Lets see how many unique entries there are
sales_unique_n = init_data["sales"].nunique()
salary_unique_n = init_data["salary"].nunique()

## 10 unique
print("Unique sale categories: {0}".format(sales_unique_n))
## 3 unique
print("Unique salary categories: {0}".format(salary_unique_n))

# Now lets break these categories out into easily digestible features for our model
sales_unique_feature_names = init_data["sales"].unique()
salary_unique_feature_names = init_data["salary"].unique()

# Function to breakdown a category into individual binary features
def break_down_features(feature_list, category, orig_data):
    for name in feature_list:
        orig_data[category+"_"+name] = [1 if x == name else 0 for _, x in enumerate(orig_data[category])]

break_down_features(sales_unique_feature_names, "sales", init_data)
break_down_features(salary_unique_feature_names, "salary", init_data)

# Now that we have added our new categories we can drop our old object ones.
init_data = init_data.drop(["sales", "salary"], axis=1)

# Lets look at the first 5 entries of what these float values are in are data
print(init_data["satisfaction_level"][:5])
print(init_data["last_evaluation"][:5])

# They seem to be just percentages but lets make sure
## 1.0
print("Max value satisfaction_level: {0}".format(init_data["satisfaction_level"].max()))
## 0.0899
print("Min value satisfaction_level: {0}".format(init_data["satisfaction_level"].min()))
## 1.0
print("Max value last_evaluation: {0}".format(init_data["last_evaluation"].max()))
## 0.3599
print("Min value last_evaluation: {0}".format(init_data["last_evaluation"].min()))

# So the values are bounded between 0 and 1

# Now lets look at what the percentage of the people that left vs the people that stayed
## 0: 0.761917;  1: 0.238083
print(init_data["left"].value_counts() / len(init_data["left"]))

# Now lets create a stratified splitting method to ensure the data is split with the same percentages
# of our feature of interest as the original data set as a whole.
def stratified_split_data(data, ratio):
    # Grab the data into its own category
    stayed_data = data.loc[data["left"] == 0]
    left_data = data.loc[data["left"] == 1]
    # mix up the data
    stayed_data = stayed_data.iloc[np.random.permutation(len(stayed_data))]
    left_data = left_data.iloc[np.random.permutation(len(left_data))]
    test_stayed_set_size = int(len(stayed_data) * ratio)
    test_left_set_size = int(len(left_data) * ratio)
    # Concatenate the partitioned data
    train_set = pd.concat([stayed_data[test_stayed_set_size:], left_data[test_left_set_size:]], ignore_index=True)
    test_set = pd.concat([stayed_data[:test_stayed_set_size], left_data[:test_left_set_size]], ignore_index=True)
    # Now mix up the concatenated data
    train_shuffled_indices = np.random.permutation(len(train_set))
    test_shuffled_indices = np.random.permutation(len(test_set))
    return train_set.iloc[train_shuffled_indices], test_set.iloc[test_shuffled_indices]

train_set, test_set = stratified_split_data(init_data, 0.2)

# Now lets make sure we still have the same percentages
print(train_set["left"].value_counts() / len(train_set["left"]))

data = (train_set.drop("left", axis=1)).values
data_labels = train_set["left"].values
data_labels = data_labels.reshape([len(data_labels), 1])

num_features = data.shape[1]
n_samples = data.shape[0]

X_init = tf.placeholder(tf.float32, [None, num_features])
Y_init = tf.placeholder(tf.float32, [None, 1])

#w_1 = tf.Variable(tf.random_normal([num_features, 10]))
#b_1 = tf.Variable(tf.random_normal([10]))

#layer_1 = tf.sigmoid(tf.add(tf.matmul(X_init, w_1), b_1))

w_2 = tf.Variable(tf.truncated_normal([num_features, 1], stddev=0.01))
b_2 = tf.Variable(tf.truncated_normal([1], stddev=0.01))

output_layer = tf.nn.softmax(tf.add(tf.matmul(X_init, w_2), b_2))

#cost = -tf.reduce_mean(tf.multiply(Y_init, tf.log(output_layer)) )

cost = tf.reduce_mean(tf.pow(tf.subtract(output_layer, Y_init), 2))

## mess around with learning rate 
optimizer = tf.train.GradientDescentOptimizer(1e-1).minimize(cost)

init = tf.global_variables_initializer()

sess = tf.Session()

sess.run(init)

loss_values = []


num_epochs = 500
batch_size = 100
count = len(data)
for epoch in range(num_epochs):
    start_n = 0
    c = None
    _, c = sess.run([optimizer, cost], feed_dict={X_init:data, Y_init:data_labels})
#    while start_n < count:
#        _, c = sess.run([optimizer, cost], feed_dict={X_init:data[start_n:(start_n + batch_size)], Y_init:data_labels[start_n:(start_n + batch_size)]})
#        sys.stdout.write("Batch:{0}/{1} cost:{2}\r".format(start_n+batch_size, count, c))
#        sys.stdout.flush()
#        start_n += batch_size
#        loss_values.append(c)
#    print("")
    sys.stdout.write("Epoch: {0}/{1} cost: {2}\r".format(epoch+1, num_epochs, c))
    sys.stdout.flush()
#    print("")


## right now getting final cost around 0.00132
print("Final cost = {0} weights: {1} biases: {2}".format(sess.run(cost, feed_dict={X_init:data, Y_init:data_labels}), sess.run(w_2), sess.run(b_2) ) )


# Lets take a look at the confusion matrix
predictions = sess.run(output_layer, feed_dict={X_init:data})

print(predictions[:5])
print(data_labels[:5])


def confusion_matrix(pred_data, act_data, threshold=0.7):
    stayed_true = 0
    stayed_false = 0
    left_true = 0
    left_false = 0
    for i in range(len(pred_data)):
        if pred_data[i][0] >= threshold and act_data[i][0] == 1:
            left_true += 1
        elif pred_data[i][0] < threshold and act_data[i][0] == 1:
            left_false += 1
        elif pred_data[i][0] >= threshold and act_data[i][0] == 0:
            stayed_false += 1
        elif pred_data[i][0] < threshold and act_data[i][0] == 0:
            stayed_true += 1
    print("Stayed True: {0}\nStayed False: {1}\nLeft True: {2}\nLeft False: {3}".format(stayed_true, stayed_false, left_true, left_false))

confusion_matrix(predictions, data_labels)



## test is getting comparable numbers as well
## However lets test the precision and recall and see what is happening
test_data = (test_set.drop("left", axis=1)).values
test_data_labels = test_set["left"].values
test_data_labels = test_data_labels.reshape([len(test_data_labels), 1])
print("Cost for test data: {0}".format(sess.run(cost, feed_dict={X_init:test_data, Y_init:test_data_labels}) ) )

import matplotlib.pyplot as plt

plt.plot(loss_values)
plt.show()


sess.close()










