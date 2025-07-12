from lsp_mcp_server.graph import DeepGraph
from lsp_mcp_server.document import Document
from lsp_mcp_server.lsps.python import PythonLangServer

class Scanner:
    def __init__(self, lsp):
        self.graph = DeepGraph()
        self.lsp = lsp

    def scan(self, doc: Document):
        """Scan a document and build a graph from the symbols it yields."""
        for symbol in doc:
            print(symbol)
            self.graph.add_symbol(symbol)

if __name__ == "__main__":
    pylsp = PythonLangServer("/Users/nahemah1022/NVIDIA/proj/aistore")
    doc = Document(
        filepath='/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/obj/object.py',
        # filepath='/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/request_client.py',
        lsp=pylsp,
    )
    scr = Scanner(lsp=pylsp)
    scr.scan(doc)
