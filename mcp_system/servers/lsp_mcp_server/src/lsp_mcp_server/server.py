import logging
import re
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path

from lsprotocol.types import SymbolKind
from typing import Union, Annotated
from lsp_mcp_server.lsps.python import PythonLangServer
from lsp_mcp_server.graph import Symbol, Position

logger = logging.getLogger(__name__)

# -- Pydantic Input Models --

class FileReader(BaseModel):
    file_path: str

class SymbolLocator(BaseModel):
    file_path: str
    keyword: str

class ShowDefinition(BaseModel):
    line_num: int
    character_num: int
    keyword: str
    file_path: str

class HoverInformation(BaseModel):
    line_num: int
    character_num: int
    keyword: str
    file_path: str

class References(BaseModel):
    line_num: int
    character_num: int
    keyword: str
    file_path: str

class DocumentSymbols(BaseModel):
    file_path: str
    kind_filter: Annotated[
        Union[SymbolKind, list[SymbolKind], None],
        Field(
            description="Optional symbol kind(s) to include (e.g., Function, Variable, Class).",
            json_schema_extra={
                "examples": ["Function", ["Function", "Class"]],
                "type": ["integer", "array"],
                "items": {"enum": [e.name for e in SymbolKind]},
            },
        ),
    ] = None

# -- Tool Enum --

class LSPTools(str, Enum):
    ShowDefinition = "show_definition"
    HoverInformation = "hover_information"
    References = "references"
    DocumentSymbols = "document_symbols"
    FileReader = "file_reader"
    SymbolLocator = "symbol_extractor"

# -- Server and Handlers --

async def serve(repository: Path) -> None:
    pylsp = PythonLangServer(root_uri=str(repository))
    server = Server("lsp-mcp-server")
    logger.debug("repository initialized at host path %s", repository)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=LSPTools.ShowDefinition,
                description="Finds the definition of the given keyword in the specified file by querying the LSP server.",
                inputSchema=ShowDefinition.model_json_schema()
            ),
            Tool(
                name=LSPTools.HoverInformation,
                description="Retrieves hover information (e.g., type or documentation) for the given keyword in the specified file by querying the LSP server.",
                inputSchema=HoverInformation.model_json_schema()
            ),
            Tool(
                name=LSPTools.References,
                description="Retrieves all references (including definition) to the given symbol in the codebase. This includes variable usages, function calls, and class references depending on context.",
                inputSchema=References.model_json_schema()
            ),
            Tool(
                name=LSPTools.DocumentSymbols,
                description="Retrieves symbols defined in the given file, optionally filtering by symbol kind(s). kind_filter: Optional single or list of SymbolKind values to include (e.g., Function, Variable).",
                inputSchema=DocumentSymbols.model_json_schema()
            ),
            Tool(
                name=LSPTools.FileReader,
                description="Read and return the content of the entire file at the given filepath",
                inputSchema=FileReader.model_json_schema()
            ),
            Tool(
                name=LSPTools.SymbolLocator,
                description="Return all symbols that matches to the keyword in the given filepath",
                inputSchema=SymbolLocator.model_json_schema()
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        logger.debug(f"Calling tool: {name}, args: {arguments}")

        match name:
            case LSPTools.ShowDefinition:
                result = pylsp.show_definition(
                    line=arguments["line_num"],
                    character=arguments["character_num"],
                    keyword=arguments["keyword"],
                    path=arguments["file_path"],
                )
                return [TextContent(type="text", text=result.__str__())]

            case LSPTools.HoverInformation:
                result = pylsp.hover(
                    line=arguments["line_num"],
                    character=arguments["character_num"],
                    keyword=arguments["keyword"],
                    path=arguments["file_path"],
                )
                return [TextContent(type="text", text=result.__str__())]

            case LSPTools.References:
                result = pylsp.references(
                    line=arguments["line_num"],
                    character=arguments["character_num"],
                    keyword=arguments["keyword"],
                    path=arguments["file_path"],
                )
                return [TextContent(type="text", text=result.__str__())]

            case LSPTools.DocumentSymbols:
                result = pylsp.document_symbols(
                    path=arguments["file_path"]
                )
                return [TextContent(type="text", text=result.__str__())]

            case LSPTools.FileReader:
                try:
                    with open(arguments['file_path'], 'r') as file:
                        content = file.read()
                    return [TextContent(type="text", text=content)]
                except FileNotFoundError:
                    print(f"Error: The file at {arguments['file_path']} was not found.")
            
            case LSPTools.SymbolLocator:
                keyword, file_path = arguments['keyword'], arguments['file_path']
                matches = []
                context_size = 3
                context = []
                pattern = r'\b' + re.escape(keyword) + r'\b'
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line_number, line in enumerate(file, start=0):
                        if len(context) == context_size:
                            context.pop(0)
                        context.append(line)
                        for match in re.finditer(pattern, line):
                            column_number = match.start()
                            symbol = Symbol(
                                name=keyword,
                                context='\n'.join(context),  # Join the context list into a single string
                                position=Position(line=line_number, character=column_number)
                            )
                            matches.append(symbol)
                    return [TextContent(type="text", text=json.dumps([symbol.dict() for symbol in matches]))]
            case _:
                raise ValueError(f"Unknown tool: {name}")

    options = server.create_initialization_options()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
