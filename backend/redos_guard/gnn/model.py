"""
ReDoS Guard — 3-Class Severity GNN Classifier
==============================================
A Graph Neural Network model that screens NFA graphs for regular expression
ambiguity severity (0: Linear / Safe, 1: Polynomial, 2: Exponential).

Architecture:
- Input: Node features X [N, 8], Edge index [2, E], Edge features [E, 4]
- Two Message-Passing Graph Convolutional Layers with normalized adjacency and self-loops
- ReLU activations + Dropout
- Global Pooling (Concat of Global Mean + Global Max pooling -> 64-dim graph embedding)
- Multi-Layer Perceptron (MLP) classification head predicting 3-class logits
"""

from typing import Optional, Tuple
import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from backend.redos_guard.gnn.constants import (
    REDOS_NODE_FEATURE_DIM,
    REDOS_EDGE_FEATURE_DIM,
    NUM_RISK_CLASSES,
)


class GraphConvLayer(nn.Module):
    """
    Message-passing graph convolution layer:
      H^(l+1) = D^(-1/2) A D^(-1/2) H^(l) W
    Includes self-loops and degree normalization. Pure PyTorch without
    external C++ extensions.
    """

    def __init__(self, in_features: int, out_features: int, bias: bool = True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.Tensor(in_features, out_features))
        if bias:
            self.bias = nn.Parameter(torch.Tensor(out_features))
        else:
            self.register_parameter("bias", None)
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        if self.bias is not None:
            fan_in, _ = nn.init._calculate_fan_in_and_fan_out(self.weight)
            bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
            nn.init.uniform_(self.bias, -bound, bound)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        num_nodes = x.size(0)
        adj = torch.zeros((num_nodes, num_nodes), device=x.device, dtype=torch.float32)

        if edge_index.size(1) > 0:
            src, dst = edge_index[0], edge_index[1]
            weights = (
                edge_weight
                if edge_weight is not None
                else torch.ones(edge_index.size(1), device=x.device)
            )
            adj.index_put_((src, dst), weights, accumulate=True)

        # Self-loops
        adj = adj + torch.eye(num_nodes, device=x.device)

        # Degree normalization: D^(-1/2) A D^(-1/2)
        degree = adj.sum(dim=1)
        deg_inv_sqrt = degree.pow(-0.5)
        deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.0
        norm_adj = deg_inv_sqrt.unsqueeze(1) * adj * deg_inv_sqrt.unsqueeze(0)

        support = torch.matmul(x, self.weight)
        out = torch.matmul(norm_adj, support)

        if self.bias is not None:
            out = out + self.bias
        return out


class ReDoSGNNClassifier(nn.Module):
    """
    3-Class GNN Classifier for screening regular expression ambiguity severity.
    Predicts logits over [Linear (0), Polynomial (1), Exponential (2)].
    """

    def __init__(
        self,
        in_node_features: int = REDOS_NODE_FEATURE_DIM,
        hidden_dim: int = 32,
        num_classes: int = NUM_RISK_CLASSES,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.conv1 = GraphConvLayer(in_node_features, hidden_dim)
        self.conv2 = GraphConvLayer(hidden_dim, hidden_dim)

        self.dropout = nn.Dropout(p=dropout)

        # Readout maps concatenated mean and max pooling (2 * hidden_dim) to logits
        pooled_dim = hidden_dim * 2
        self.fc1 = nn.Linear(pooled_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        edge_weight: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass producing classification logits.

        Args:
            x: Node features [N, in_node_features]
            edge_index: Edge index [2, E]
            edge_weight: Optional edge weights [E]

        Returns:
            Logits tensor of shape [1, num_classes]
        """
        h1 = F.relu(self.conv1(x, edge_index, edge_weight))
        h1 = self.dropout(h1)
        h2 = F.relu(self.conv2(h1, edge_index, edge_weight))

        # Global pooling (mean + max)
        if h2.size(0) == 0:
            mean_pool = torch.zeros((1, h2.size(1)), device=x.device)
            max_pool = torch.zeros((1, h2.size(1)), device=x.device)
        else:
            mean_pool = torch.mean(h2, dim=0, keepdim=True)
            max_pool = torch.max(h2, dim=0, keepdim=True).values

        graph_embedding = torch.cat([mean_pool, max_pool], dim=1)

        out = F.relu(self.fc1(graph_embedding))
        out = self.dropout(out)
        logits = self.fc2(out)
        return logits

    def predict_risk(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> Tuple[str, float, torch.Tensor]:
        """
        Returns (predicted_risk_class, confidence, probabilities_tensor).
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x, edge_index)
            probs = F.softmax(logits, dim=-1).squeeze(0)
            pred_idx = int(torch.argmax(probs).item())
            confidence = float(probs[pred_idx].item())
            class_names = ["linear", "polynomial", "exponential"]
            return class_names[pred_idx], confidence, probs
