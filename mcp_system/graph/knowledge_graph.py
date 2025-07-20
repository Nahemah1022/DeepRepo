from typing import Dict, Union, List, Optional, TYPE_CHECKING
from dataclasses import dataclass, field
import json

if TYPE_CHECKING:
    from graph.code_block import CodeBlock
    from graph.document import Document

# Positional Information
@dataclass
class Position:
    line: int
    character: int

    def key(self):
        return f"{self.line}:{self.character}"

@dataclass
class Location:
    uri: str
    position: Position

    def key(self) -> str:
        return f"{self.uri}:{self.position.key()}"

@dataclass
class Range:
    start: Position
    end: Position

# Functional Information
@dataclass
class Index:
    name: str
    location: Location
    context: str

@dataclass
class Function(Location):
    name: str
    code_block: 'CodeBlock'
    # built from graph
    index: Optional[Index] = None
    dependencies: List[Index] = field(default_factory=list)

    def add_dependency(self, index: Index):
        if not index:
            return
        self.dependencies.append(index)

@dataclass
class Variable(Location):
    index: Optional[Index] = None
    name: str = ""

# Graph Information
@dataclass
class Symbol:
    name: str
    pos: Position
    decl: Location

# decl_map[KEY_0] = F
# F.index.uri.key() = KEY_0
# F.dependencies = [decl_map[KEY_!].index, decl_map[KEY_2].index, ...]
@dataclass
class KnowledgeGraph:
    base_uri: str
    docs_map: Dict[str, 'Document'] = field(default_factory=dict) # only for parsing
    decl_map: Dict[str, Union[Function, Variable]] = field(default_factory=dict)

    def add_decl(self, decl: Union[Function, Variable]):
        self.decl_map[decl.key()] = decl

    def to_dot(self, output_file: str = "knowledge_graph.dot") -> str:
        """
        Export the graph to DOT format for visualization with Graphviz.
        
        Args:
            output_file: Path to save the DOT file
            
        Returns:
            The DOT content as a string
        """
        dot_content = ["digraph KnowledgeGraph {"]
        dot_content.append("  rankdir=LR;")
        dot_content.append("  node [shape=box, style=filled, fontname=\"Arial\"];")
        dot_content.append("  edge [fontname=\"Arial\", fontsize=10];")
        dot_content.append("")
        
        # Add nodes
        for node_key, node in self.decl_map.items():
            # Trim base_uri from display key for shorter labels
            display_key = node_key
            if hasattr(self, 'base_uri') and self.base_uri and node_key.startswith(self.base_uri):
                display_key = node_key[len(self.base_uri):]
            
            if isinstance(node, Function):
                # Function nodes in blue
                label = f"{node.name}\\n{display_key}"
                dot_content.append(f'  "{node_key}" [label="{label}", fillcolor="lightblue"];')
            elif isinstance(node, Variable):
                # Variable nodes in green
                label = f"{node.name}\\n{display_key}"
                dot_content.append(f'  "{node_key}" [label="{label}", fillcolor="lightgreen"];')
        
        dot_content.append("")
        
        # Add edges (dependencies)
        for node_key, node in self.decl_map.items():
            if isinstance(node, Function) and node.dependencies:
                for dep_index in node.dependencies:
                    if dep_index and hasattr(dep_index, 'location'):
                        dep_key = dep_index.location.key()
                        if dep_key in self.decl_map:
                            dot_content.append(f'  "{node_key}" -> "{dep_key}";')
        
        dot_content.append("}")
        
        dot_string = "\n".join(dot_content)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(dot_string)
        
        return dot_string

    def to_json(self, output_file: str = "knowledge_graph.json") -> str:
        """
        Export the graph to JSON format for visualization with other tools.
        
        Args:
            output_file: Path to save the JSON file
            
        Returns:
            The JSON content as a string
        """
        graph_data = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes
        for node_key, node in self.decl_map.items():
            node_data = {
                "id": node_key,
                "type": type(node).__name__,
                "name": getattr(node, 'name', ''),
                "uri": node.uri,
                "position": {
                    "line": node.position.line,
                    "character": node.position.character
                }
            }
            
            if isinstance(node, Function):
                node_data["dependencies_count"] = len(node.dependencies)
                if node.index:
                    node_data["index_name"] = node.index.name
                    node_data["index_context"] = node.index.context
            
            graph_data["nodes"].append(node_data)
        
        # Add edges
        for node_key, node in self.decl_map.items():
            if isinstance(node, Function) and node.dependencies:
                for dep_index in node.dependencies:
                    if dep_index and hasattr(dep_index, 'location'):
                        dep_key = dep_index.location.key()
                        if dep_key in self.decl_map:
                            edge_data = {
                                "source": node_key,
                                "target": dep_key,
                                "source_name": node.name,
                                "target_name": dep_index.name
                            }
                            graph_data["edges"].append(edge_data)
        
        json_string = json.dumps(graph_data, indent=2)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(json_string)
        
        return json_string

    def print_summary(self):
        """
        Print a human-readable summary of the graph structure.
        """
        print(f"Knowledge Graph Summary:")
        print(f"Total nodes: {len(self.decl_map)}")
        
        function_count = sum(1 for node in self.decl_map.values() if isinstance(node, Function))
        variable_count = sum(1 for node in self.decl_map.values() if isinstance(node, Variable))
        
        print(f"Functions: {function_count}")
        print(f"Variables: {variable_count}")
        
        total_dependencies = 0
        for node in self.decl_map.values():
            if isinstance(node, Function):
                total_dependencies += len(node.dependencies)
        
        print(f"Total dependencies: {total_dependencies}")
        print(f"Average dependencies per function: {total_dependencies / function_count if function_count > 0 else 0:.2f}")
        
        print("\nTop functions by dependencies:")
        function_deps = [(node.name, len(node.dependencies)) 
                        for node in self.decl_map.values() 
                        if isinstance(node, Function)]
        function_deps.sort(key=lambda x: x[1], reverse=True)
        
        for name, deps in function_deps[:10]:  # Top 10
            print(f"  {name}: {deps} dependencies")

    def visualize(self, format: str = "dot", output_file: Optional[str] = None):
        """
        Convenience method to visualize the graph.
        
        Args:
            format: Either "dot" or "json"
            output_file: Optional output file path
        """
        if format.lower() == "dot":
            if not output_file:
                output_file = "knowledge_graph.dot"
            dot_content = self.to_dot(output_file)
            print(f"Graph exported to DOT format: {output_file}")
            print("To visualize with Graphviz, run:")
            print(f"  dot -Tpng {output_file} -o {output_file.replace('.dot', '.png')}")
            print("Or use online tools like: https://dreampuf.github.io/GraphvizOnline/")
            
        elif format.lower() == "json":
            if not output_file:
                output_file = "knowledge_graph.json"
            json_content = self.to_json(output_file)
            print(f"Graph exported to JSON format: {output_file}")
            print("You can visualize this JSON with tools like:")
            print("- NetworkX (Python)")
            print("- D3.js")
            print("- Gephi")
            
        else:
            raise ValueError("Format must be 'dot' or 'json'")
        
        # Also print summary
        print("\n" + "="*50)
        self.print_summary()
