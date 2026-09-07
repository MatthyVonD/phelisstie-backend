"""Py and NumPy"""
import numpy as np
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]]) # np (numpy) is a library for numerical computations in Python, often used for working with arrays and matrices. In this code snippet, `X` represents the input data for a neural network, specifically the inputs for the XOR problem. Each row of `X` corresponds to a different input combination of two binary variables (0 or 1). The corresponding output `y` is defined as the expected result of the XOR operation for each input combination.
y = np.array([[0], [1], [1], [0]])  # XOR output

# Activation function sigmoid
def sigmoid(x): # sigmoid is a mathematical function that maps any real-valued number into the range (0, 1). It is commonly used as an activation function in neural networks to introduce non-linearity.
    """Return the sigmoid activation for the given input."""
    return 1 / (1 + np.exp(-x))  # .exp is the exponential function, which raises the mathematical constant e (approximately 2.71828) to the power of the input value. The sigmoid function is often used in neural networks to introduce non-linearity and squash the output values into a range between 0 and 1.

def sigmoid_derivative(x):
    s = sigmoid(x)
    return s * (1 - s)

# Arquitecture
w1  = np.random.rand(2, 4)  # Weights for the first layer, .rand generates random numbers from a uniform distribution over [0, 1). In this code snippet, `w1` represents the weights for the first layer of the neural network. It is a 2x4 matrix, where each row corresponds to an input feature (2 features in this case), and each column corresponds to a neuron in the first layer (4 neurons in this case). The weights are initialized randomly to break symmetry and allow the network to learn different features during training.
b1 = np.zeros((1, 4))  # Bias for the first layer, .zeros creates an array filled with zeros. In this code snippet, `b1` represents the bias for the first layer of the neural network. It is a 1x4 array, where each element corresponds to a neuron in the first layer (4 neurons in this case). The bias is initialized to zero, which means that initially, the neurons will not have any additional offset added to their weighted inputs.
w2 = np.random.rand(4, 1)  # Weights for the second layer
b2 = np.zeros((1, 1))  # Bias for the second layer

# Training
learning_rate = 0.5
for epoch in range(10000):
    # Forward
    z1 = X @ w1 + b1 # Linear combination for the first layer
    a1 = sigmoid(z1) # Apply activation function
    z2 = a1 @ w2 + b2 # Linear combination for the second layer
    a2 = sigmoid(z2) # Apply activation function
    # Error
    error = y - a2 # Calculate the error between the predicted output and the actual output
    # Backpropagation
    dz2 = error * sigmoid_derivative(z2) # Calculate the gradient for the second layer
    dw2 = a1.T @ dz2 # Calculate the weight update for the second layer
    db2 = np.sum(dz2, axis=0, keepdims=True) # Calculate the bias update for the second layer
    dz1 = dz2 @ w2.T * sigmoid_derivative(z1) # Calculate the gradient for the first layer
    dw1 = X.T @ dz1 # Calculate the weight update for the first layer
    db1 = np.sum(dz1, axis=0, keepdims=True) # Calculate the bias update for the first layer
    # Update weights and biases
    w2 += learning_rate * dw2 # Update the weights for the second layer
    b2 += learning_rate * db2 # Update the bias for the second layer
    w1 += learning_rate * dw1 # Update the weights for the first layer
    b1 += learning_rate * db1 # Update the bias for the first layer

# Testing
print("predictions:\n", a2, "\nobjective:\n", np.round(a2)) 
# Print the final predictions and the expected output after training the neural network. The predictions are the output of the network after applying the sigmoid activation function to the final layer's linear combination, while the objective is the actual expected output for the XOR problem.
