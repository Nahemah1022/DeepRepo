from typing import List, Iterator
from lsp_mcp_server.graph import Symbol, Position, Location
from lsp_mcp_server.lsps.base import LangServer

class CodeBlock:
    def __init__(self, lines: List[str], lsp: LangServer, uri: str, base_line_number: int):
        self.base_line_number = base_line_number
        self.lines = lines
        self.lsp = lsp
        self.uri = uri

    def __str__(self):
        return '\n'.join(self.lines)

    def _strip_comments(self, line: str) -> str:
        """Strip comments from a line of code."""
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

    def _strip_strings(self, line: str) -> str:
        """Strip string literals from a line of code."""
        string_delimiters = self.lsp.string_delimiters
        
        if self.in_string and self.current_string_end is not None:
            # Find the end delimiter for the current string type
            end_idx = line.find(self.current_string_end)
            if end_idx != -1:
                self.in_string = False
                string_end = self.current_string_end
                self.current_string_end = None
                return line[end_idx + len(string_end):].strip()
            return ""

        # Check for start of any string type
        earliest_start = -1
        earliest_delimiter = None
        
        for str_start, str_end in string_delimiters:
            start_idx = line.find(str_start)
            if start_idx != -1 and (earliest_start == -1 or start_idx < earliest_start):
                earliest_start = start_idx
                earliest_delimiter = (str_start, str_end)
        
        if earliest_start != -1 and earliest_delimiter is not None:
            str_start, str_end = earliest_delimiter
            end_idx = line[earliest_start + len(str_start):].find(str_end)
            if end_idx != -1:
                # String start and end are on the same line
                return line[:earliest_start] + line[earliest_start + len(str_start) + end_idx + len(str_end):]
            else:
                self.in_string = True
                self.current_string_end = str_end
                return line[:earliest_start]  # Keep everything before the start of the string
        
        return line

    def _process_word(self, word: str, line_number: int, symbol_idx: int) -> Iterator[Symbol]:
        """Process a word and yield Symbol if it's not a reserved keyword and has a definition."""
        if word not in self.lsp.keywords:
            # Try to find definition for this symbol
            res = self.lsp.show_definition(
                line=line_number,
                character=symbol_idx,
                keyword=word,
                path=self.uri,
            )
            # print(f"word: {word}, line: {line_number}, char: {symbol_idx}, res: {res}, uri: {self.uri}")
            if res and isinstance(res, list):
                loc = res[0] # TODO: handle multiple definitions
                sym = Symbol(
                    name=word,
                    pos=Position(line=line_number, character=symbol_idx),
                    decl=Location(
                        uri=loc.uri, 
                        position=Position(
                            line=loc.range.start.line, 
                            character=loc.range.start.character
                        )
                    ),
                )
                yield sym

    def _parse_symbols_from_line(self, line: str, line_number: int) -> Iterator[Symbol]:
        """Parse symbols from a single line and yield Symbol objects."""
        separators = self.lsp.separators

        symbol_idx = None  # symbol starting index
        for char_number, char in enumerate(line):
            if char in separators:
                if symbol_idx is not None:
                    word = line[symbol_idx:char_number]
                    yield from self._process_word(word, line_number, symbol_idx)
                    symbol_idx = None  # Reset symbol_idx
            else:
                if symbol_idx is None:
                    symbol_idx = char_number  # Start of a new symbol
        
        # Handle the case where a symbol is at the end of the line
        if symbol_idx is not None:
            word = line[symbol_idx:]
            yield from self._process_word(word, line_number, symbol_idx)

    def __iter__(self):
        self.line_number = 0
        self.in_multiline_comment = False
        self.in_string = False
        self.current_string_end = None
        self._symbol_buffer = []
        return self

    def __next__(self):        
        # If we have symbols in the buffer, return the next one
        if self._symbol_buffer:
            return self._symbol_buffer.pop(0)
        
        while True:
            # print(f"self.line_number: {self.line_number}, len(self.lines): {len(self.lines)}")
            if self.line_number == len(self.lines): # End of code block
                raise StopIteration

            current_line = self.lines[self.line_number]
            stripped_line = self._strip_comments(current_line)
            stripped_line = self._strip_strings(stripped_line)
            if stripped_line:
                # Collect all symbols from this line into the buffer
                self._symbol_buffer = list(self._parse_symbols_from_line(stripped_line, self.line_number + self.base_line_number))
                if self._symbol_buffer:
                    self.line_number += 1
                    return self._symbol_buffer.pop(0)

            self.line_number += 1

