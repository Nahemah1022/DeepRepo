import logging
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)

# -- Pydantic Input Models --

class ShowDefinition(BaseModel):
    file_path: str
    line_num: int
    column_num: int

# -- Tool Enum --

class LSPTools(str, Enum):
    ShowDefinition = "show_definition"

# -- Actual Tool Implementations --

def show_definition() -> str:
    return f"example definition"

# -- Server and Handlers --

async def serve(endpoint: str) -> None:
    server = Server("lsp-mcp-server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name=LSPTools.ShowDefinition, description="Show the definition of the given symbol", inputSchema=ShowDefinition.schema()),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        logger.debug(f"Calling tool: {name}, args: {arguments}")

        match name:
            case LSPTools.ShowDefinition:
                result = show_definition()
                return [TextContent(type="text", text="\n".join(result))]

            case _:
                raise ValueError(f"Unknown tool: {name}")

    options = server.create_initialization_options()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options, raise_exceptions=True)
