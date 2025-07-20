# Knowledge Graph Visualization

This document explains how to use the visualization features added to the `KnowledgeGraph` class to help debug and understand your graph construction logic.

## Overview

The `KnowledgeGraph` class now includes several methods to export and visualize the graph structure:

- `to_dot()` - Exports to Graphviz DOT format
- `to_json()` - Exports to JSON format for other visualization tools
- `print_summary()` - Prints a human-readable summary
- `visualize()` - Convenience method that combines the above

## Quick Start

### 1. Basic Usage

```python
from lsp_mcp_server.graph import KnowledgeGraph

# After building your graph...
graph = KnowledgeGraph(base_uri="file:///path/to/your/project/")
# ... add your nodes and dependencies ...

# Print a summary
graph.print_summary()

# Export to DOT format
graph.visualize("dot", "my_graph.dot")

# Export to JSON format
graph.visualize("json", "my_graph.json")
```

### 2. Test the Visualization

Run the test script to see the visualization in action:

```bash
cd mcp_system/servers/lsp_mcp_server
python test_visualization.py
```

## Visualization Formats

### DOT Format (Graphviz)

The DOT format creates a directed graph that can be visualized with Graphviz.

**To visualize:**
1. Install Graphviz: `brew install graphviz` (macOS) or `apt-get install graphviz` (Ubuntu)
2. Generate PNG: `dot -Tpng my_graph.dot -o my_graph.png`
3. Or use online tools: https://dreampuf.github.io/GraphvizOnline/

**Features:**
- Function nodes are colored light blue
- Variable nodes are colored light green
- Dependencies are shown as directed edges
- Node labels include both name and shortened key (base_uri prefix trimmed) for identification

### JSON Format

The JSON format provides a structured representation that can be used with various tools.

**Structure:**
```json
{
  "nodes": [
    {
      "id": "node_key",
      "type": "Function|Variable",
      "name": "node_name",
      "uri": "file_path",
      "position": {"line": 1, "character": 0},
      "dependencies_count": 2,
      "index_name": "index_name",
      "index_context": "context"
    }
  ],
  "edges": [
    {
      "source": "source_node_key",
      "target": "target_node_key",
      "source_name": "source_name",
      "target_name": "target_name"
    }
  ]
}
```

**Tools that can visualize this JSON:**
- NetworkX (Python)
- D3.js (web)
- Gephi (desktop application)
- Cytoscape (desktop application)

## Graph Summary

The `print_summary()` method provides a quick overview:

```
Knowledge Graph Summary:
Total nodes: 15
Functions: 8
Variables: 7
Total dependencies: 23
Average dependencies per function: 2.88

Top functions by dependencies:
  main_function: 5 dependencies
  helper_function: 3 dependencies
  utility_function: 2 dependencies
```

## Debugging Your Graph Construction

### Common Issues to Check

1. **Missing Dependencies**: If a function should depend on something but the edge doesn't appear, check:
   - Is the dependency's `index.location.key()` returning a valid key?
   - Is that key present in `decl_map`?
   - Is the dependency being added correctly with `add_dependency()`?

2. **Node Types**: Verify that:
   - Functions have the correct `name` and `code_block`
   - Variables have the correct `name`
   - All nodes have valid `uri` and `position` values

3. **Index Consistency**: Ensure that:
   - Each node's `index.location.key()` matches its own key in `decl_map`
   - Dependencies reference valid indices

### Example Debugging Session

```python
# After building your graph
graph = KnowledgeGraph()
# ... build graph ...

# Check what's in the graph
print(f"Total nodes: {len(graph.decl_map)}")

# Check specific nodes
for key, node in graph.decl_map.items():
    print(f"Node: {key}")
    print(f"  Type: {type(node).__name__}")
    print(f"  Name: {getattr(node, 'name', 'N/A')}")
    if isinstance(node, Function):
        print(f"  Dependencies: {len(node.dependencies)}")
        for dep in node.dependencies:
            print(f"    - {dep.name} -> {dep.location.key()}")

# Export for visualization
graph.visualize("dot", "debug_graph.dot")
```

## Integration with Your Existing Code

The visualization methods are designed to work with your existing graph structure:

```python
# Your existing graph building code
graph = KnowledgeGraph()

# After adding all your declarations
for decl in your_declarations:
    graph.add_decl(decl)

# Add dependencies
for func in your_functions:
    for dep in func.dependencies:
        func.add_dependency(dep)

# Now visualize to verify everything is correct
graph.visualize("dot", "final_graph.dot")
graph.print_summary()
```

## Tips for Large Graphs

For very large graphs, consider:

1. **Filtering**: Only visualize specific parts of the graph
2. **Sampling**: Export a subset of nodes for initial testing
3. **Hierarchical**: Use tools like Gephi that can handle large graphs with clustering
4. **Interactive**: Use D3.js for interactive exploration of large graphs

## Troubleshooting

### Common Errors

1. **"Key not found in decl_map"**: A dependency references a node that doesn't exist
2. **"Invalid position"**: Position values are outside expected ranges
3. **"Missing index"**: A node doesn't have an associated index

### Performance

- DOT format is fast and good for graphs up to ~1000 nodes
- JSON format is more flexible but may be slower for very large graphs
- Consider using specialized graph databases for graphs with >10,000 nodes 