import asyncio
from fastmcp import Client
from fastmcp.client.logging import LogMessage

async def log_handler(message: LogMessage):
    level = message.level.upper()
    logger = message.logger or 'server'
    data = message.data
    print(f"[{level}] {logger}: {data}")

async def main():
    async with Client("http://localhost:8000/sse", log_handler=log_handler) as client:
        tools = await client.list_tools()
        print(f"Available tools: {tools}")
        result = await client.call_tool("HoverInformation", {
            "file_path": "/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/obj/object.py",
            "line_num": 64,
            "character_num": 9,
            "keyword": "Object",
        })
        print(f"Result: {result}")

asyncio.run(main())
