import torch
import torch.nn as nn
import torch_geometric.nn as nn_geo

class GraphSAGE(nn.Module):
    def __init__(self):
        super(GraphSAGE, self).__init__()
        self.conv1 = nn_geo.SAGEConv(5, 10, aggr="add")
        self.conv2 = nn_geo.SAGEConv(10, 20, aggr="add")
    
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = torch.relu(x)
        x = self.conv2(x, edge_index)
        return torch.relu(x)