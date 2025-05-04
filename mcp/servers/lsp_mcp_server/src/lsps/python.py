import os
import json
import time

from lsprotocol import types
from base import LangServer

class PythonLangServer(LangServer):
    def __init__(self, rootUri: str):
        super().__init__(cmd=["pyright-langserver", "--stdio"], rootUri=rootUri)

    @property
    def language_id(self) -> str:
        return "python"

    def locator(self, line: int, character: int, keyword: str, path: str) -> types.Position:
        return types.Position(line=line, character=character)

if __name__ == "__main__":
    pylsp = PythonLangServer(
        rootUri='/Users/nahemah1022/Projects/DeepRepo/mcp/servers/lsp_mcp_server/src/lsps'
    )
    definition = pylsp.show_definition(
        path="/Users/nahemah1022/Projects/DeepRepo/mcp/servers/lsp_mcp_server/src/lsps/python.py", 
        line=22, character=26, keyword="show_definition",
    )
    print(definition)

    hover = pylsp.hover(
        path="/Users/nahemah1022/Projects/DeepRepo/mcp/servers/lsp_mcp_server/src/lsps/python.py", 
        line=22, character=26, keyword="hover",
    )
    print(hover)
