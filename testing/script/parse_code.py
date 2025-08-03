import ast
import json
import argparse
import os

class CodeParser(ast.NodeVisitor):
    """
    An AST node visitor that walks the abstract syntax tree and extracts
    information about classes and functions.
    """
    def __init__(self, file_path: str):
        self.file_path = os.path.abspath(file_path)
        self.nodes = []
        # Read the source code once for use with get_source_segment
        with open(file_path, 'r', encoding='utf-8') as f:
            self.source_code = f.read()

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Extracts information for a class definition node.
        """
        # The ast.get_source_segment function reliably gets the full source
        # of the node, including its decorator list and body.
        source = ast.get_source_segment(self.source_code, node)
        
        self.nodes.append({
            "type": "Class",
            "name": node.name,
            "uri": self.file_path,
            "code_content": source
        })
        # IMPORTANT: This allows the visitor to find functions inside this class
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Extracts information for a function or method definition node.
        """
        source = ast.get_source_segment(self.source_code, node)
        
        self.nodes.append({
            "type": "Function",
            "name": node.name,
            "uri": self.file_path,
            "code_content": source
        })
        # We don't need to visit children of functions for this task.

def analyze_file(file_path: str) -> list:
    """
    Analyzes a single Python file and returns a list of nodes.
    
    Args:
        file_path (str): The path to the Python file.

    Returns:
        list: A list of dictionaries, each representing a class or function.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Error: The file '{file_path}' was not found.")
    
    print(f"🔬 Analyzing {file_path}...")
    
    # Read the file content and parse it into an AST
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()
        tree = ast.parse(source_code)

    # Create the visitor and have it walk the tree
    parser = CodeParser(file_path)
    parser.visit(tree)
    
    print(f"✅ Analysis complete. Found {len(parser.nodes)} nodes.")
    return parser.nodes

def main():
    """
    Main function to handle command-line arguments and orchestrate the analysis.
    """
    cli_parser = argparse.ArgumentParser(
        description="Parse a Python file to extract class and function definitions as JSON."
    )
    cli_parser.add_argument(
        "file_path",
        type=str,
        help="The path to the Python file to analyze."
    )
    cli_parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Optional. Path to save the JSON output file. Prints to console if not provided."
    )
    
    args = cli_parser.parse_args()

    try:
        # Get the list of nodes from the analysis
        all_nodes = analyze_file(args.file_path)
        
        # Convert the list to a JSON string
        json_output = json.dumps(all_nodes, indent=2)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"💾 Output successfully saved to {args.output}")
        else:
            # Print the final JSON output to the console
            print("\n--- JSON Output ---")
            print(json_output)

    except (FileNotFoundError, SyntaxError) as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()