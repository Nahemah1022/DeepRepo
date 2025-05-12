import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path

from lsprotocol.types import SymbolKind
from typing import Union, Annotated
from mcp_system.servers.lsp_mcp_server.src.lsp_mcp_server.lsps.python import PythonLangServer
# from mcp.servers.lsp_mcp_server.src.lsp_mcp_server.lsps.python import PythonLangServer

logger = logging.getLogger(__name__)

# -- Pydantic Input Models --

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
    path: str
    kind_filter: Annotated[
        Union[SymbolKind, list[SymbolKind], None],
        Field(
            description="Optional symbol kind(s) to include (e.g., Function, Variable, Class).",
            json_schema_extra={
                "examples": ["Function", ["Function", "Class"]],
                "type": ["string", "array"],
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
                logger.debug(f"[RETURNED] {result.__str__()}")
                return [TextContent(type="text", text=result.__str__())]

            case LSPTools.HoverInformation:
                result = pylsp.hover(
                    line=arguments["line_num"],
                    character=arguments["character_num"],
                    keyword=arguments["keyword"],
                    path=arguments["file_path"],
                )
                logger.debug(f"[RETURNED] {result.__str__()}")
                return [TextContent(type="text", text=result.__str__())]

            case LSPTools.References:
                result = pylsp.references(
                    line=arguments["line_num"],
                    character=arguments["character_num"],
                    keyword=arguments["keyword"],
                    path=arguments["file_path"],
                )
                logger.debug(f"[RETURNED] {result.__str__()}")
                return [TextContent(type="text", text=result.__str__())]

            case LSPTools.DocumentSymbols:
                result = pylsp.document_symbols(
                    path=arguments["file_path"]
                )
                logger.debug(f"[RETURNED] {result.__str__()}")
                return [TextContent(type="text", text=result.__str__())]

            case _:
                raise ValueError(f"Unknown tool: {name}")

    options = server.create_initialization_options()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
