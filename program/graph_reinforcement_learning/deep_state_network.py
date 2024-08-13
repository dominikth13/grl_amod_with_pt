from __future__ import annotations

from torch import Tensor
import torch
from torch_geometric.utils import to_undirected
from torch_geometric.data import Data

from program.action.action import Action
from program.graph_reinforcement_learning.deep_neural_network import DeepNeuralNetwork
from program.graph_reinforcement_learning.graph_sage import GraphSAGE
from program.interval.time import Time
from program.zone.zone import Zone
from program.zone.zone_graph import ZoneGraph


class DeepStateNetwork:

    def __init__(self) -> None:
        self.graph_sage = GraphSAGE()
        self.dnn = DeepNeuralNetwork()

        self.current_graph_embedding: Tensor = None
        self.current_state_values_by_action_id: dict[int, Tensor] = {}
    
    def clear(self) -> None:
        self.current_graph_embedding = None
        self.current_state_values_by_action_id = {}

    def get_state_value(
        self, action: Action, zone: Zone, time: Time
    ) -> float:
        from program.state.state import State
        zone_graph = ZoneGraph.get_instance()

        state_features = zone_graph.get_feature(zone)
        zone_id = zone.id
        normalized_time = State.get_state().current_time.to_normalized_time()
        state_embedding = Tensor(
            [
                state_features.num_orders_now,
                state_features.num_orders_before,
                state_features.num_occupied,
                state_features.num_idle,
                state_features.average_time_reduction,
                zone_id,
                normalized_time,
            ]
        )

        node = zone_graph.get_node_id(zone)
        graph_embedding = self.current_graph_embedding[node]

        combined_features = torch.cat([state_embedding, graph_embedding], dim=0)

        state_value = self.dnn(combined_features)

        # Save the q value for later
        self.current_state_values_by_action_id[action.id] = state_value

        return float(state_value.item())
    
    def calculate_graph_embedding(self, edge_index: tuple[list[int], list[int]], features: list[tuple[int, int, int, int, float]]) -> None:
        edge_index_torch = torch.tensor(edge_index, dtype=torch.long)
        edge_index_torch = to_undirected(edge_index_torch)
        x_tensor = torch.tensor(features, dtype=torch.float)

        data = Data(x=x_tensor, edge_index=edge_index_torch)

        self.current_graph_embedding = self.graph_sage(data.x, data.edge_index)

    def get_state_value_by_action_id(self, id: int) -> Tensor:
        return self.current_state_values_by_action_id[id]
    
    def load_GNN_state_dict(self, state_dict):
        self.graph_sage.load_state_dict(state_dict)
    
    def load_DNN_state_dict(self, state_dict):
        self.dnn.load_state_dict(state_dict)
    
    def get_GNN_state_dict(self):
        return self.graph_sage.state_dict()
    
    def get_DNN_state_dict(self):
        return self.dnn.state_dict()