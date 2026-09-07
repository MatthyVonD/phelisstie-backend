"""Phelisstie Neural Network"""
import torch
import torch.nn as nn

class PhelisstieNet(nn.Module):
    """A simple neural network with one linear layer."""
    def __init__(self):
        super(PhelisstieNet, self).__init__()
        self.fc1 = nn.Linear(2, 1)

    def forward(self, entrance):
        """Defines the forward pass of the network."""
        return self.fc1(entrance)

net = PhelisstieNet()
x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
y = torch.tensor([[1.0], [2.0]])
prediction = net(x)
print("Prediction:", prediction)

loss_fn = nn.MSELoss()
optimizer = torch.optim.SGD(net.parameters(), lr=0.01)

for epoch in range(500):
    optimizer.zero_grad()
    prediction = net(x)
    loss = loss_fn(prediction, y)
    loss.backward()
    optimizer.step()
    print(f"Epoch {epoch+1}, Loss: {loss.item()}")
    print("Prediction:", net(x), "\nObjective:", y)