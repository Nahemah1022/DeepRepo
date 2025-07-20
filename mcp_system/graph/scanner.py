from graph.knowledge_graph import KnowledgeGraph, Symbol, Function, Index
from graph.document import Document
from servers.lsp.servers import PythonLangServer

class Scanner:
    def __init__(self, lsp):
        self.graph = KnowledgeGraph(base_uri=lsp.root_uri)
        self.lsp = lsp

    def scan(self, entry_point: Document):
        if entry_point.uri in self.graph.docs_map:
            return
        self.graph.docs_map[entry_point.uri] = entry_point
        # print(f"document {entry_point.uri} added to graph")
        for node in entry_point.values():
            if isinstance(node, Function):
                # print(f"scanning {node.name} in document {entry_point.uri}")
                for symbol in node.code_block:
                    # print(f"symbol: {symbol.name} in {symbol.decl.key()}")
                    if not self.isinternal(symbol):
                        continue
                    if symbol.decl.uri not in self.graph.docs_map:
                        self.scan(Document(filepath=symbol.decl.uri, lsp=self.lsp))
                    definition = self.graph.docs_map[symbol.decl.uri].get(symbol.decl.key())
                    if definition and isinstance(definition, Function) and definition.key() != node.key():
                        if definition.index:
                            # print(f"adding dependency {definition.name} to {node.name}, definition.key()={definition.key()}, node.key()={node.key()}")
                            node.add_dependency(definition.index)
                node.index = Index(name=node.name, location=node, context="") # TODO: build context with code block and dependencies
                self.graph.add_decl(node)
            # self.graph.add_index(node.index)

    def isinternal(self, symbol: Symbol):
        return symbol.decl.uri.startswith(self.lsp.root_uri)

if __name__ == "__main__":
    pylsp = PythonLangServer("/Users/nahemah1022/NVIDIA/proj/aistore")
    doc = Document(
        filepath='file:///Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/client.py',
        # filepath='/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/request_client.py',
        lsp=pylsp,
    )
    scr = Scanner(lsp=pylsp)
    scr.scan(doc)
    scr.graph.visualize(format="dot", output_file="knowledge_graph.dot")
