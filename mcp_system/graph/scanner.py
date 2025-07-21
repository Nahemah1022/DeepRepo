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
        for node in entry_point.values():
            if isinstance(node, Function):
                for symbol in node.code_block:
                    if not self.isinternal(symbol):
                        continue
                    if symbol.decl.uri not in self.graph.docs_map:
                        self.scan(Document(filepath=symbol.decl.uri, lsp=self.lsp))
                    definition = self.graph.docs_map[symbol.decl.uri].get(symbol.decl.key())
                    if definition and isinstance(definition, Function):
                        if definition.key() == node.key():
                            continue
                        if definition.index: # TODO -- FIXME:if the definition is in the same document, chances are the definition is not scanned yet (not indexed yet)
                            node.add_dependency(definition.index)
                node.index = Index(name=node.name, location=node, context="") # TODO: build context with code block and dependencies
                self.graph.add_decl(node)

    def isinternal(self, symbol: Symbol):
        return symbol.decl.uri.startswith(self.lsp.root_uri) and symbol.decl.uri.find(".venv") == -1

if __name__ == "__main__":
    pylsp = PythonLangServer("/Users/nahemah1022/NVIDIA/proj/aistore")
    # pylsp = PythonLangServer("/Users/nahemah1022/Projects/DeepRepo")
    doc = Document(
        filepath='file:///Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/client.py',
        # filepath='file:///Users/nahemah1022/Projects/DeepRepo/mcp_system/graph/scanner.py',
        lsp=pylsp,
    )
    scr = Scanner(lsp=pylsp)
    scr.scan(doc)
    scr.graph.visualize(format="dot", output_file="knowledge_graph.dot")
