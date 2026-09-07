"""Backpropagation"""
import numpy as np
x = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
y = np.array([[0], [1], [1], [0]])
w1 = np.random.rand(2, 8)
b1 = np.zeros((1, 3))
w2 = np.random.rand(8, 1)
b2 = np.zeros((1, 1))

def sigmoid(x):
    """Return the sigmoid activation for the given input."""
    return 1 / (1 + np.exp(-x))

def sigmoid_derivative(x):
    """Compute the derivative of the sigmoid function."""
    s = sigmoid(x)
    return s * (1 - s)

np.random.seed(42)

W1 = np.random.rand(2, 3)
b1 = np.zeros((1, 3))
W2 = np.random.rand(3, 1)
b2 = np.zeros((1, 1))

LEARNING_RATE = 5
for epoch in range(10000):
    # Forward pass
    Z1 = x @ W1 + b1
    A1 = sigmoid(Z1)
    Z2 = A1 @ W2 + b2
    A2 = sigmoid(Z2)

    # Compute the loss
    loss = np.mean((y - A2) ** 2)

    # Backpropagation
    dZ2 = (A2 - y) * sigmoid_derivative(Z2)
    dW2 = A1.T @ dZ2
    db2 = np.sum(dZ2, axis=0, keepdims=True)

    dA1 = dZ2 @ W2.T

    dZ1 = dZ2 @ W2.T * sigmoid_derivative(Z1)
    dW1 = x.T @ dZ1
    db1 = np.sum(dZ1, axis=0, keepdims=True)

    # Update weights and biases
    W2 -= LEARNING_RATE * dW2
    b2 -= LEARNING_RATE * db2
    W1 -= LEARNING_RATE * dW1
    b1 -= LEARNING_RATE * db1

    # Print progress
    if epoch % 1000 == 0:
        print(f"Epoch {epoch}, Loss: {loss:.6f}")

print(f"\nPredictions:\n{A2}\nRedonde:\n{np.round(A2)}")
print(W1, W2)
