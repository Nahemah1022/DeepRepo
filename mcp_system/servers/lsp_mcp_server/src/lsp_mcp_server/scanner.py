from lsp_mcp_server.graph import DeepGraph, Symbol, Position
from lsp_mcp_server.lsps.python import PythonLangServer, LangServer

class Document:
    def __init__(self, filepath: str, lsp: LangServer, context_size: int = 2):
        self.uri = filepath
        self.lsp = lsp
        self.context_size = context_size
        self.context = []
        self._file = None
        self.line_number = 0

    def get_uri(self):
        return self.uri

    def get_context(self):
        return '\n'.join(self.context)


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
        keywords = self.lsp.keywords
        inlie_comment = self.lsp.inlie_comment
        mc_start, mc_end = self.lsp.multiline_comment

        for line_number, line in doc:
            inline_comment_idx = line.find(inlie_comment)
            if inline_comment_idx != -1:
                line = line[:inline_comment_idx]

            if self.in_multiline_comment:
                mc_end_idx = line.find(mc_end)
                if mc_end_idx != -1:
                    self.in_multiline_comment = False
                    line = line[:mc_end_idx]  # Keep everything after the comment end
                else:
                    continue

            mc_start_idx = line.find(mc_start)
            if mc_start_idx != -1:
                if mc_end in line[mc_start_idx+len(mc_start):]:
                    # The comment start and end are on the same line
                    line = line[:mc_start_idx] + line[line.find(mc_end) + len(mc_end):]
                else:
                    self.in_multiline_comment = True
                    line = line[:mc_start_idx]  # Keep everything before the start of the comment

            symbol_idx = None # symbol starting index
            for char_number, char in enumerate(line):
                if char in separators:
                    if symbol_idx is not None:
                        word = line[symbol_idx:char_number]
                        if word not in keywords:
                            sym = self.build_symbol(
                                path=doc.get_uri(),
                                pos=Position(line=line_number, character=symbol_idx),
                                keyword=word,
                                ctx=doc.get_context(),
                            )
                            # self.graph.add_symbol(sym)
                        symbol_idx = None  # Reset symbol_idx
                else:
                    if symbol_idx is None:
                        symbol_idx = char_number  # Start of a new symbol

    def build_symbol(self, path: str, pos: Position, keyword: str, ctx: str) -> Symbol:
        loc = self.lsp.show_definition(
            line=pos.line,
            character=pos.character,
            keyword=keyword,
            path=path,
        )
        if loc:
            print(f"word: {keyword}, loc: {loc}")
            # print(f"word: {keyword}")
        definition = None
        # return Symbol(position=pos, definition=definition, context=ctx)

if __name__ == "__main__":
    pylsp = PythonLangServer("/Users/nahemah1022/NVIDIA/proj/aistore")
    doc = Document(
        filepath='/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/obj/object.py',
        lsp=pylsp,
    )
    scr = Scanner(lsp=pylsp)
    scr.scan(doc)
