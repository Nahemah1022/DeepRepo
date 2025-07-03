from typing import Dict, List
from pydantic import BaseModel

class Position(BaseModel):
    line: int
    character: int

class Link(BaseModel):
    src: str  # name of the source Symbol
    dst: str  # name of the destination Symbol
    invoke_position: Position
    context: str

class Symbol(BaseModel):
    name: str
    position: Position
    context: str
    links: List[Link] = []  # list of outbound links

    def add_link(self, link: Link):
        self.links.append(link)

    def as_dict(self):
        return self.dict(exclude={'links'})

class DeepGraph(BaseModel):
    symbols: Dict[str, Symbol] = {}

    def add_symbol(self, name: str, pos: Position):
        self.symbols[name] = Symbol(name=name, position=pos)

    def add_link(self, src_name: str, dst_name: str, invoke_position: Position):
        src = self.symbols[src_name]
        dst = self.symbols[dst_name]
        link = Link(src=src_name, dst=dst_name, invoke_position=invoke_position)
        src.add_link(link)