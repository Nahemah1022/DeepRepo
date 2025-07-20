from pathlib import Path
import urllib.parse
import keyword
import typing

from lsprotocol.types import SymbolKind, Position
from servers.lsp.servers.base import LangServer

class PythonLangServer(LangServer):
    def __init__(self, root_uri: str):
        super().__init__(cmd=["pyright-langserver", "--stdio"], root_uri=root_uri)

    @property
    def language_id(self) -> str:
        return "python"

    @property
    def separators(self) -> typing.Set[str]:
        return set(' \n\t.,!?;(){}[]<>:\'#*/=@')

    @property
    def keywords(self) -> typing.Set[str]:
        reserved_keywords = set(keyword.kwlist)
        custom_keywords = {"self", "setter", "getter", "+", "-", "def", "class"}
        built_in_types = {"str", "bool", "float", "int", "complex", "tuple", "dict"}
        typing_keywords = set(typing.__dict__.keys())
        built_in_keywords = set(dir(__builtins__))
        return reserved_keywords | custom_keywords | built_in_types | typing_keywords | built_in_keywords

    @property
    def inlie_comment(self) -> str:
        return "#"

    @property
    def multiline_comment(self) -> typing.Tuple[str, str]:
        return ('"""', '"""')

    @property
    def string_delimiters(self) -> typing.List[typing.Tuple[str, str]]:
        return [('"', '"'), ("'", "'")]

    def is_literal(self, word: str) -> bool:
        """Check if the word is a literal value (like a number, string, etc.)."""
        try:
            eval_word = eval(word)
            if isinstance(eval_word, (int, float, str, bool, complex, type(None))):
                return True
        except:
            pass
        return False

    def locator(self, line: int, character: int, keyword: str, path: str) -> Position:
        if path.startswith("file://"):
            parsed = urllib.parse.urlparse(path)
            file_path = Path(urllib.parse.unquote(parsed.path))
        else:
            file_path = Path(path)

        with file_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        def normalize_line_index(idx: int) -> int:
            return max(0, min(idx, len(lines) - 1))

        candidate_lines = [
            normalize_line_index(line), # 0-based index
            normalize_line_index(line - 1), # 1-based index
        ]

        nearby_lines = sorted(set(normalize_line_index(i) for i in range(line - 5, line + 6)))

        for idx in candidate_lines + nearby_lines:
            expanded = lines[idx].expandtabs(4)
            col = expanded.find(keyword)
            if col != -1:
                return Position(line=idx, character=col)

        fallback_line = normalize_line_index(line - 1)
        fallback_char = max(0, character - 1)
        return Position(line=fallback_line, character=fallback_char)

if __name__ == "__main__":
    workspace_root = Path("/Users/nahemah1022/NVIDIA/proj/aistore/python").resolve()
    pylsp = PythonLangServer(root_uri=str(workspace_root))

    # definition = pylsp.show_definition(
    #     path="/Users/nahemah1022/Projects/DeepRepo/mcp/servers/lsp_mcp_server/src/lsps/python.py", 
    #     line=49, character=24, keyword="show_definition",
    # )
    # print(definition)

    # show_hover = pylsp.hover(
    #     path="/Users/nahemah1022/Projects/DeepRepo/mcp/servers/lsp_mcp_server/src/lsps/python.py", 
    #     line=49, character=24, keyword="show_definition",
    # )
    # print(show_hover)

    # ref = pylsp.references(
    #     path="/Users/nahemah1022/Projects/DeepRepo/mcp/servers/lsp_mcp_server/src/lsps/python.py", 
    #     line=49, character=24, keyword="show_definition",
    # )
    # print(ref)

    symbols = pylsp.document_symbols(
        path="/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/obj/object_reader.py",
        kind_filter=[SymbolKind.Function, SymbolKind.Class]
    )
    print(symbols)
