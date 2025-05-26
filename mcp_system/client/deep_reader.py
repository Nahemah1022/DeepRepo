import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)



class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
    # methods will go here


    async def connect_to_server(self, server_script_path: str, args: list[str]):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        server_params = StdioServerParameters(
            command=server_script_path,
            args=args,
            env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools until terminate is called."""
        messages = [
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
                "title": "terminate",
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        #a = [{'name': 'get_alerts', 'description': 'Get weather alerts for a US state.\n\n    Args:\n        state: Two-letter US state code (e.g. CA, NY)\n    ', 'input_schema': {'properties': {'state': {'title': 'State', 'type': 'string'}}, 'required': ['state'], 'title': 'get_alertsArguments', 'type': 'object'}}, {'name': 'get_forecast', 'description': 'Get weather forecast for a location.\n\n    Args:\n        latitude: Latitude of the location\n        longitude: Longitude of the location\n    ', 'input_schema': {'properties': {'latitude': {'title': 'Latitude', 'type': 'number'}, 'longitude': {'title': 'Longitude', 'type': 'number'}}, 'required': ['latitude', 'longitude'], 'title': 'get_forecastArguments', 'type': 'object'}}] and response meta=None nextCursor=None tools=[Tool(name='get_alerts', description='Get weather alerts for a US state.\n\n    Args:\n        state: Two-letter US state code (e.g. CA, NY)\n    ', inputSchema={'properties': {'state': {'title': 'State', 'type': 'string'}}, 'required': ['state'], 'title': 'get_alertsArguments', 'type': 'object'}), Tool(name='get_forecast', description='Get weather forecast for a location.\n\n    Args:\n        latitude: Latitude of the location\n        longitude: Longitude of the location\n    ', inputSchema={'properties': {'latitude': {'title': 'Latitude', 'type': 'number'}, 'longitude': {'title': 'Longitude', 'type': 'number'}}, 'required': ['latitude', 'longitude'], 'title': 'get_forecastArguments', 'type': 'object'})]
        available_tools = [terminate_tool] + [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in real_tools]
        print(available_tools)

        # available_tools = [{
        #     "name": tool.name,
        #     "description": tool.description,
        #     "input_schema": tool.inputSchema
        # } for tool in response.tools]

        final_text = []

        while True:
            # Claude generation
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=messages,
                tools=available_tools,
                system=(
                            "You are a helpful assistant that can use external tools to solve user problems. "
                            "You can call tools multiple times if needed, but must call the 'terminate' tool to end the task. "
                            "Think step by step, and only terminate once you’ve provided a complete solution."
                        )
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

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == 'quit':
                    break
                
                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <server_script> [args_for_server_script...]")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1], sys.argv[2:])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
