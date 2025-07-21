from graph.code_block import CodeBlock
from graph.knowledge_graph import Position, Variable, Function
from servers.lsp.servers.base import LangServer
from typing import Union
from lsprotocol.types import SymbolKind

class Document(dict[str, Union[Variable, Function]]):
    def __init__(self, filepath: str, lsp: LangServer):
        self.uri = filepath
        self.lsp = lsp
        self._extract_symbols()

    def _extract_symbols(self):
        lsp_symbols = self.lsp.document_symbols(self.uri)
        for lsp_sym in lsp_symbols:
            match lsp_sym.kind:
                case SymbolKind.Variable | SymbolKind.Constant:
                    definition = Variable(
                        name=lsp_sym.name,
                        uri=lsp_sym.location.uri,
                        position=Position(line=lsp_sym.location.range.start.line, character=lsp_sym.location.range.start.character)
                    )
                    self[definition.key()] = definition
                case SymbolKind.Method | SymbolKind.Function:
                    code_block = self.get_code_block(lsp_sym.location.uri, lsp_sym.location.range.start.line, lsp_sym.location.range.end.line)
                    definition = Function(
                        name=lsp_sym.name,
                        code_block=code_block,
                        uri=lsp_sym.location.uri,
                        position=Position(line=lsp_sym.location.range.start.line, character=lsp_sym.location.range.start.character + 4), # shift over the `def ` keyword
                    )
                    self[definition.key()] = definition
                # case SymbolKind.Class:
                #     code_block = self.get_code_block(lsp_sym.location.uri, lsp_sym.location.range.start.line, lsp_sym.location.range.end.line)
                #     definition = Function(
                #         name=lsp_sym.name,
                #         code_block=code_block,
                #         uri=lsp_sym.location.uri,
                #         position=Position(line=lsp_sym.location.range.start.line, character=lsp_sym.location.range.start.character + 6), # shift over the `class ` keyword
                #     )
                #     self[definition.key()] = definition
    
    def get_code_block(self, uri: str, start_line: int, end_line: int) -> CodeBlock:
        if uri.startswith("file://"):
            uri = uri[7:] # remove file:// prefix
        code_lines = []
        with open(uri, 'r', encoding='utf-8') as file:
            for current_line_num, line in enumerate(file):
                if current_line_num > end_line:
                    break
                if current_line_num >= start_line:
                    code_lines.append(line.rstrip('\n'))
        return CodeBlock(code_lines, self.lsp, uri, base_line_number=start_line)

    def get_uri(self):
        return self.uri

