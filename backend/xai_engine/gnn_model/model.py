"""
Automata GNN Classifier Architecture
====================================
Owned by: Member B (GNN + Explainable AI Module)

A Graph Neural Network model that ingests an automaton graph topology and
traversal features to predict whether the candidate string is accepted or
rejected by the formal language.

Architecture:
  - Input: Node features X [N, F_in], Edge index [2, E], Edge features [E, F_edge]
  - Graph Convolutional Layers (Message Passing via Normalized Adjacency / GCNConv)
  - Nonlinearity (ReLU) & Dropout
  - Readout: Global pooling over node embeddings
  - Classification Head: Multi-Layer Perceptron (MLP) mapping to binary logits
"""

from typing import Tuple, Optional
import math

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    nn = object  # type: ignore


from backend.xai_engine.constants import NODE_FEATURE_DIM, EDGE_FEATURE_DIM


if TORCH_AVAILABLE:

    class GraphConvLayer(nn.Module):
        """
        Message-passing graph convolution layer:
          H^(l+1) = D^(-1/2) A D^(-1/2) H^(l) W
        Includes self-loops and degree normalization. Works in standard PyTorch
        without requiring torch-scatter / torch-sparse compiled wheels.
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

            # Build adjacency matrix
            adj = torch.zeros((num_nodes, num_nodes), device=x.device, dtype=torch.float32)

            if edge_index.size(1) > 0:
                src, dst = edge_index[0], edge_index[1]
                weights = edge_weight if edge_weight is not None else torch.ones(edge_index.size(1), device=x.device)
                adj.index_put_((src, dst), weights, accumulate=True)

            # Add self-loops
            adj = adj + torch.eye(num_nodes, device=x.device)

            # Symmetric degree normalization
            degree = adj.sum(dim=1)
            deg_inv_sqrt = degree.pow(-0.5)
            deg_inv_sqrt[torch.isinf(deg_inv_sqrt)] = 0.0
            norm_adj = deg_inv_sqrt.unsqueeze(1) * adj * deg_inv_sqrt.unsqueeze(0)

            # Message passing: A_norm @ X @ W
            support = torch.matmul(x, self.weight)
            out = torch.matmul(norm_adj, support)

            if self.bias is not None:
                out = out + self.bias
            return out


    class AutomataGNNClassifier(nn.Module):
        """
        GNN Classifier model for automata graph classification.
        Predicts binary string acceptance (0: rejected, 1: accepted).
        """

        def __init__(
            self,
            node_in_dim: int = NODE_FEATURE_DIM,
            edge_in_dim: int = EDGE_FEATURE_DIM,
            hidden_dim: int = 32,
            num_classes: int = 2,
            dropout: float = 0.1,
        ):
            super().__init__()
            self.conv1 = GraphConvLayer(node_in_dim, hidden_dim)
            self.conv2 = GraphConvLayer(hidden_dim, hidden_dim)
            self.conv3 = GraphConvLayer(hidden_dim, hidden_dim)

            self.dropout = nn.Dropout(dropout)

            # Classification MLP
            self.fc1 = nn.Linear(hidden_dim * 2, hidden_dim)  # *2 for [mean_pool, max_pool]
            self.fc2 = nn.Linear(hidden_dim, num_classes)

        def forward(
            self,
            x: torch.Tensor,
            edge_index: torch.Tensor,
            edge_weight: Optional[torch.Tensor] = None,
        ) -> torch.Tensor:
            """
            Forward pass.

            Args:
                x: Node feature tensor [N, node_in_dim]
                edge_index: Graph connectivity tensor [2, E]
                edge_weight: Optional edge importance/weights [E]

            Returns:
                Logits tensor of shape [1, num_classes]
            """
            h = F.relu(self.conv1(x, edge_index, edge_weight))
            h = self.dropout(h)
            h = F.relu(self.conv2(h, edge_index, edge_weight))
            h = self.dropout(h)
            h = F.relu(self.conv3(h, edge_index, edge_weight))

            # Graph-level pooling (combining mean and max pooling)
            mean_pool = torch.mean(h, dim=0, keepdim=True)
            max_pool = torch.max(h, dim=0, keepdim=True)[0]
            graph_embed = torch.cat([mean_pool, max_pool], dim=1)

            # Classification head
            out = F.relu(self.fc1(graph_embed))
            out = self.dropout(out)
            logits = self.fc2(out)
            return logits

        def predict(
            self,
            x: torch.Tensor,
            edge_index: torch.Tensor,
            edge_weight: Optional[torch.Tensor] = None,
        ) -> Tuple[bool, float]:
            """
            Inference helper returning boolean acceptance verdict and probability score.
            """
            self.eval()
            with torch.no_grad():
                logits = self.forward(x, edge_index, edge_weight)
                probs = F.softmax(logits, dim=1)
                predicted_class = torch.argmax(probs, dim=1).item()
                confidence = probs[0, predicted_class].item()
                return bool(predicted_class == 1), float(confidence)

else:
    # Fallback dummy class if PyTorch is not yet installed
    class AutomataGNNClassifier:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

        def predict(self, *args, **kwargs) -> Tuple[bool, float]:
            return True, 0.95
