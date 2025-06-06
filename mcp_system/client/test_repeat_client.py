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
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        response = await self.session.list_tools()
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools]

        logging.info("BOWEN YANG DEBUG logging info available_tools {} and response {}".format(available_tools, response))
        # Initial Claude API call
        response = self.anthropic.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=messages,
            tools=available_tools
        )

        logging.info("BOWEN YANG FIRST round response {} response cntent is {}".format(response, response.content))
        # Process response and handle tool calls
        final_text = []

        assistant_message_content = []
        for content in response.content:
            if content.type == 'text':
                logging.info("BOWEN YANG DEBUG trigger text")
                final_text.append(content.text)
                assistant_message_content.append(content)
                logging.info("BOWEN YANG DEBUG FINAL text in text mode: {}, assistent message content {}".format(final_text, assistant_message_content))
            elif content.type == 'tool_use':
                logging.info("BOWEN YANG DEBUG trigger tool_use")
                tool_name = content.name
                tool_args = content.input

                # Execute tool call
                result = await self.session.call_tool(tool_name, tool_args)
                logging.info("BOWEN YANG INFO result from tool {} result: {}".format(result, tool_name))
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                assistant_message_content.append(content)
                messages.append({
                    "role": "assistant",
                    "content": assistant_message_content
                })

                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": content.id,
                            "content": result.content
                        }
                    ]
                })

                logging.info("BOWEN YANG DEBUG messages after wrapping from tool_use {}".format(messages))
                # Get next response from Claude
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=messages,
                    tools=available_tools
                )
                logging.info("BOWEN YANG DEBUG response from anothrpic {}".format(response))
                final_text.append(response.content[0].text)
                logging.info("BOWEN YANG DEBUG final text after tool_use {}".format(response, final_text))

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