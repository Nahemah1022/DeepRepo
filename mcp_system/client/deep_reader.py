import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

import logging

load_dotenv()  # load environment variables from .env


from dotenv import load_dotenv
import logging

async def process_query(self, query: str) -> str:
    """Process a query using Claude and available tools until terminate is called."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that can use external tools to solve user problems. "
                "You can call tools multiple times if needed, but must call the 'terminate' tool to end the task. "
                "Think step by step, and only terminate once you’ve provided a complete solution."
            )
        },
        {
            "role": "user",
            "content": query
        }
    ]

    # Get real tools from MCP session
    response = await self.session.list_tools()
    real_tools = response.tools

    # Inject terminate tool
    terminate_tool = {
        "name": "terminate",
        "description": "Call this tool when you are completely done and ready to finish.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }

    available_tools = [terminate_tool] + [{
        "name": tool.name,
        "description": tool.description,
        "input_schema": tool.inputSchema
    } for tool in real_tools]

    final_text = []

    while True:
        # Claude generation
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        assistant_content = []
        tool_called = False

        for content in response.content:
            if content.type == 'text':
                final_text.append(content.text)
                assistant_content.append(content)

            elif content.type == 'tool_use':
                tool_called = True
                tool_name = content.name
                tool_args = content.input

                assistant_content.append(content)
                messages.append({
                    "role": "assistant",
                    "content": assistant_content
                })

                # Check for terminate
                if tool_name == "terminate":
                    logging.info("Claude has chosen to terminate.")
                    return "\n".join(final_text)

                # Real tool call
                result = await self.session.call_tool(tool_name, tool_args)
                logging.info(f"Called tool {tool_name} with args {tool_args} → {result.content}")

                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": result.content
                    }]
                })

        if not tool_called:
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })
            break  # No more tools, stop

    return "\n".join(final_text)
