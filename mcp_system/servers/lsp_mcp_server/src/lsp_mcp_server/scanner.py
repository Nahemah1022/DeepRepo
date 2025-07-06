from lsp_mcp_server.graph import DeepGraph, Symbol, Position, Function, Variable, Location, Range
from lsp_mcp_server.lsps.python import PythonLangServer, LangServer

from lsprotocol.types import SymbolKind
from lsprotocol.types import Location as LSPLocation
from typing import Dict, Union

class Document:
    def __init__(self, filepath: str, lsp: LangServer, context_size: int = 2):
        self.uri = filepath
        self.lsp = lsp
        self.context_size = context_size
        self.context = []
        self._file = None
        self.line_number = 0
        self.def_map: Dict[str, Union[Function, Variable]] = {}

        if lsp:
            self._retrieve_symbols()

    def get_uri(self):
        return self.uri

    def get_context(self):
        return '\n'.join(self.context)

    def _retrieve_symbols(self):
        lsp_symbols = self.lsp.document_symbols(self.uri)
        for lsp_sym in lsp_symbols:
            # print(lsp_sym.location)
            match lsp_sym.kind:
                case SymbolKind.Variable | SymbolKind.Constant:
                    definition = Variable(
                        name=lsp_sym.name,
                        uri=lsp_sym.location.uri,
                        position=Position(line=lsp_sym.location.range.start.line, character=lsp_sym.location.range.start.character)
                    )
                    self.def_map[definition.index()] = definition
                case SymbolKind.Method | SymbolKind.Function:
                    definition = Function(
                        name=lsp_sym.name,
                        uri=lsp_sym.location.uri,
                        position=Position(line=lsp_sym.location.range.start.line, character=lsp_sym.location.range.start.character),
                        range=Range(
                            start=Position(line=lsp_sym.location.range.start.line, character=lsp_sym.location.range.start.character),
                            end=Position(line=lsp_sym.location.range.end.line, character=lsp_sym.location.range.end.character)
                        )
                    )
        # print(self.def_map)

    def __iter__(self):
        self._file = open(self.uri, 'r', encoding='utf-8')
        # Reset context and index
        self.context = []
        self.line_number = 0
        return self

    def __next__(self):
        current_line = self._file.readline()
        if current_line == '':  # End of file
            self._file.close()
            raise StopIteration
        self.context.append(current_line.strip())
        if len(self.context) > self.context_size:
            self.context.pop(0)  # Remove the oldest context

        result = (self.line_number, current_line)
        self.line_number += 1
        return result

class Scanner:
    def __init__(self, lsp):
        self.graph = DeepGraph()
        self.lsp = lsp
        self.context_size = 3
        self.in_multiline_comment = False

    def scan(self, doc: Document):
        separators = self.lsp.separators
        reserved_keywords = self.lsp.keywords

        for line_number, line in doc:
            line = self._strip_comments(line)
            if not line:
                continue

            symbol_idx = None # symbol starting index
            for char_number, char in enumerate(line):
                if char in separators:
                    if symbol_idx is not None:
                        word = line[symbol_idx:char_number]
                        if word not in reserved_keywords:
                            print(word)
                            res = self.lsp.show_definition(
                                line=line_number,
                                character=symbol_idx,
                                keyword=word,
                                path=doc.get_uri(),
                            )
                            if res and isinstance(res, list): # TODO: res could be a single Location?
                                for loc in res:
                                    sym = Symbol(
                                        pos=Position(line=line_number, character=symbol_idx),
                                        decl=Location(uri=loc.uri, position=Position(line=loc.range.start.line, character=loc.range.start.character)),
                                        # context=doc.get_context(),
                                        context=""
                                    )
                                    print(sym)
                                    self.graph.add_symbol(sym)

                        symbol_idx = None  # Reset symbol_idx
                else:
                    if symbol_idx is None:
                        symbol_idx = char_number  # Start of a new symbol        

    def _strip_comments(self, line: str) -> str:
        mc_start, mc_end = self.lsp.multiline_comment
        inline_comment_idx = line.find(self.lsp.inlie_comment)
        if inline_comment_idx != -1:
            line = line[:inline_comment_idx]

        if self.in_multiline_comment:
            end_idx = line.find(mc_end)
            if end_idx != -1:
                self.in_multiline_comment = False
                return line[end_idx + len(mc_end):].strip()
            return ""

        start_idx = line.find(mc_start)
        if start_idx != -1:
            end_idx = line[start_idx+len(mc_start):].find(mc_end)
            if end_idx != -1:
                # Comment start and end are on the same line
                return line[:start_idx] + line[start_idx + len(mc_start) + end_idx + len(mc_end):]
            else:
                self.in_multiline_comment = True
                return line[:start_idx]  # Keep everything before the start of the comment
        
        return line

if __name__ == "__main__":
    pylsp = PythonLangServer("/Users/nahemah1022/NVIDIA/proj/aistore")
    doc = Document(
        filepath='/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/obj/object.py',
        # filepath='/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/request_client.py',
        lsp=pylsp,
    )
    scr = Scanner(lsp=pylsp)
    scr.scan(doc)
