"""Vectors and Matrices"""
import numpy as np
# X = np.array([2, 3])
# W = np.array([0.5, -0.2])
# b = 0.1

# z = X @ W + b

# print(z)

X = np.array([1,2,3,4])
Y = np.array([5,10,15,20])
w = 0.0
b = 0.0

LEARNING_RATE = 0.01
for epoch in range(1000):
    #prediction
    y_pred = X * w + b
    #error
    error = y_pred - Y
    #loss
    loss = np.mean(error ** 2)
    #gradient
    dw = np.mean(2 * X * error)
    db = np.mean(2 * error)

    #update parameters
    w -= LEARNING_RATE * dw
    b -= LEARNING_RATE * db
