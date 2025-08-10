import json
from preprocess.preprocess import Preprocess
from data_models.cache_agent_data_models import NodeInfo, CacheAgentState
from typing import List
from collections import deque

class CacheAgentPreprocess(Preprocess):
    def __init__(self, file_path: str):
        self.graph_path = file_path
        self.graph: List[CacheAgentState] = []

    def loadgraph(self):
        """
        Loads a graph from a JSON file, sorts it topologically,
        and populates the self.graph attribute.
        """
        # 1. Load the raw data from the JSON file
        with open(self.graph_path, 'r') as f:
            raw_nodes = json.load(f)

        if not raw_nodes:
            return

        # 2. Prepare data structures for sorting
        # Create a quick-lookup map from index to node data
        nodes_by_index = {node['index']: node for node in raw_nodes}
        
        # The 'dependencies_count' is the in-degree of each node.
        # We copy it to a mutable list to track changes.
        in_degree = [node['dependencies_count'] for node in raw_nodes]

        # Build the reverse graph (successors map) to know which nodes to update.
        # Format: {dependency_index: [list of nodes that depend on it]}
        successors = {i: [] for i in range(len(raw_nodes))}
        for node in raw_nodes:
            for dep_index in node['dependencies']:
                successors[dep_index].append(node['index'])

        # 3. Initialize the queue with all nodes that have an in-degree of 0
        # These are the nodes with no dependencies.
        queue = deque([node['index'] for node in raw_nodes if node['dependencies_count'] == 0])
        
        sorted_indices = []
        while queue:
            # Dequeue a node and add it to our sorted list
            u_index = queue.popleft()
            sorted_indices.append(u_index)

            # For each successor of the dequeued node, decrement its in-degree
            for v_index in successors[u_index]:
                in_degree[v_index] -= 1
                # If a successor's in-degree becomes 0, it's ready to be processed
                if in_degree[v_index] == 0:
                    queue.append(v_index)
        
        # Sanity check for cycles. If not all nodes are in the sorted list, a cycle exists.
        if len(sorted_indices) != len(raw_nodes):
            raise ValueError("A cycle was detected in the dependency graph. Cannot perform topological sort.")

        # 4. Build the final list of CacheAgentState objects in the correct order
        final_graph = []
        for index in sorted_indices:
            node_data = nodes_by_index[index]
            
            # Create the main NodeInfo object for the current node
            current_node_info = NodeInfo(
                type=node_data['type'],
                name=node_data['name'],
                path=node_data['uri'],
                code_content=node_data['code_content']
            )

            # Create a list of NodeInfo objects for its dependencies
            dependency_nodes_info = []
            for dep_index in node_data['dependencies']:
                dep_data = nodes_by_index[dep_index]
                dependency_nodes_info.append(
                    NodeInfo(
                        type=dep_data['type'],
                        name=dep_data['name'],
                        path=dep_data['uri'],
                        code_content=dep_data['code_content']
                    )
                )
            
            # Create the final CacheAgentState object and append it
            final_graph.append(
                CacheAgentState(
                    node=current_node_info,
                    dependencies=dependency_nodes_info
                )
            )

        self.graph = final_graph
        print(f"Graph loaded and sorted successfully. Total nodes: {len(self.graph)}")