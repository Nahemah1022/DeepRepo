from typing import Dict, Union
from pydantic import BaseModel

class Position(BaseModel):
    line: int
    character: int

    def index(self):
        return f"{self.line}:{self.character}"

class Location(BaseModel):
    uri: str
    position: Position

    def index(self) -> str:
        return self.position.index()

class Range(BaseModel):
    start: Position
    end: Position

class Function(Location):
    name: str
    range: Range

class Variable(Location):
    name: str

class Symbol(BaseModel):
    name: str
    pos: Position
    decl: Location
    context: str

class DeepGraph(BaseModel):
    symbols: Dict[str, Symbol] = {}

    def add_symbol(self, sym: Symbol):
        self.symbols[sym.decl.index()] = sym
