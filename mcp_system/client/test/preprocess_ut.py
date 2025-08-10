
import unittest
import json
from unittest.mock import patch, mock_open

# Assume the classes are in these locations. Adjust imports as needed.
from preprocess.preprocess import Preprocess
from data_models.cache_agent_data_models import NodeInfo, CacheAgentState
from preprocess.cache_agent_preprocess import CacheAgentPreprocess
# The Test Suite
class TestCacheAgentPreprocess(unittest.TestCase):

    def setUp(self):
        """A helper to define sample data once."""
        # This is a valid graph where Node C (2) depends on A (0) and B (1).
        # Expected topological order: A and B (in any order), then C.
        self.valid_graph_data = [
            {"index": 0, "type": "Function", "name": "Node A", "uri": "/a.py", "code_content": "def a(): pass", "dependencies_count": 0, "dependencies": []},
            {"index": 1, "type": "Function", "name": "Node B", "uri": "/b.py", "code_content": "def b(): pass", "dependencies_count": 0, "dependencies": []},
            {"index": 2, "type": "Class", "name": "Node C", "uri": "/c.py", "code_content": "class C: pass", "dependencies_count": 2, "dependencies": [0, 1]}
        ]

        # This graph has a cycle: 0 -> 1 -> 0
        self.cyclic_graph_data = [
            {"index": 0, "type": "Function", "name": "Node A", "uri": "/a.py", "code_content": "def a(): pass", "dependencies_count": 1, "dependencies": [1]},
            {"index": 1, "type": "Function", "name": "Node B", "uri": "/b.py", "code_content": "def b(): pass", "dependencies_count": 1, "dependencies": [0]}
        ]

    def test_loadgraph_successful_sort(self):
        """
        Tests that a valid dependency graph is loaded and sorted topologically.
        """
        # Arrange: Mock reading the valid JSON data from a file
        mock_json_string = json.dumps(self.valid_graph_data)
        m = mock_open(read_data=mock_json_string)

        with patch("builtins.open", m):
            # Act: Create instance and call the method
            sut = CacheAgentPreprocess(file_path="dummy/path/graph.json")
            sut.loadgraph()

            # Assert: Check the results
            self.assertEqual(len(sut.graph), 3)

            # Check topological order: The first two nodes must be A and B.
            # We use a set because their relative order doesn't matter.
            first_two_node_names = {sut.graph[0].node.name, sut.graph[1].node.name}
            self.assertEqual(first_two_node_names, {"Node A", "Node B"})
            
            # The last node must be C.
            self.assertEqual(sut.graph[2].node.name, "Node C")

            # Assert the structure of the dependent node
            node_c_state = sut.graph[2]
            self.assertEqual(node_c_state.node.name, "Node C")
            self.assertEqual(len(node_c_state.dependencies), 2)
            dependency_names = {dep.name for dep in node_c_state.dependencies}
            self.assertEqual(dependency_names, {"Node A", "Node B"})

    def test_loadgraph_cycle_detection(self):
        """
        Tests that a ValueError is raised if the graph contains a cycle.
        """
        # Arrange: Mock reading the cyclic JSON data
        mock_json_string = json.dumps(self.cyclic_graph_data)
        m = mock_open(read_data=mock_json_string)

        with patch("builtins.open", m):
            sut = CacheAgentPreprocess(file_path="dummy/path/cyclic.json")
            
            # Act & Assert: Check that the specific error is raised
            with self.assertRaisesRegex(ValueError, "A cycle was detected"):
                sut.loadgraph()

    def test_loadgraph_empty_file(self):
        """
        Tests that the function handles an empty JSON array gracefully.
        """
        # Arrange: Mock an empty JSON list
        m = mock_open(read_data="[]")

        with patch("builtins.open", m):
            # Act
            sut = CacheAgentPreprocess(file_path="dummy/path/empty.json")
            sut.loadgraph()

            # Assert
            self.assertEqual(len(sut.graph), 0)
            self.assertIsInstance(sut.graph, list)

# This allows the test to be run from the command line
if __name__ == '__main__':
    # You would need to paste or import the CacheAgentPreprocess class here
    # for this file to be runnable standalone.
    unittest.main(exit=False)