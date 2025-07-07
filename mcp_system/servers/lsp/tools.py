from typing import Annotated
from pydantic import Field
from fastmcp import Context

from fmcp import mcp
from servers import PythonLangServer

pylsp = None

def register_tools(uri: str):
    global pylsp
    pylsp = PythonLangServer(root_uri=uri)

@mcp.tool
async def ShowDefinition(
    file_path: Annotated[str, Field(description="The absolute path of the file to query symbol's definition")],
    line_num: Annotated[int, Field(description="The zero-indexed row number of the line in the file")],
    character_num: Annotated[int, Field(description="The zero-indexed column number of the character in the file")],
    keyword: str,
    ctx: Context
) -> str:
    """Query the definition of the symbol at the given position in the file."""
    await ctx.debug("Starting analysis of numerical data")

    try:
        result = pylsp.show_definition(
            line=line_num,
            character=character_num,
            keyword=keyword,
            path=file_path,
        )
        return result.__str__()
    except Exception as e:
        await ctx.error(f"failed: {str(e)}")
        raise

@mcp.tool
async def HoverInformation(
    file_path: Annotated[str, Field(description="The absolute path of the file to query symbol's definition")],
    line_num: Annotated[int, Field(description="The zero-indexed row number of the line in the file")],
    character_num: Annotated[int, Field(description="The zero-indexed column number of the character in the file")],
    keyword: str,
    ctx: Context
) -> str:
    """Query the definition of the symbol at the given position in the file."""
    await ctx.debug("Starting analysis of numerical data")

    try:
        result = pylsp.hover(
            line=line_num,
            character=character_num,
            keyword=keyword,
            path=file_path,
        )
        return result.__str__()
    except Exception as e:
        await ctx.error(f"failed: {str(e)}")
        raise