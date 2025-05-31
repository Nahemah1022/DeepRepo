from typing import Dict, List, Union
from pydantic import BaseModel

class Position(BaseModel):
    line: int
    character: int

class Location(BaseModel):
    uri: str
    position: Position

class Range(BaseModel):
    start: Position
    end: Position

class Function(BaseModel):
    name: str
    location: Location
    range: Range

class Variable(BaseModel):
    name: str
    location: Location

class Symbol(BaseModel):
    position: Position
    definition: Union[Function, Variable]
    context: str

class DeepGraph(BaseModel):
    symbols: Dict[str, Symbol] = {}

    def add_symbol(self, sym: Symbol):
        self.symbols[sym.definition.name] = sym
