# Create server parameters for stdio connection
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
load_dotenv()

server_params = StdioServerParameters(
    command="python",
    # Make sure to update to the full absolute path to your math_server.py file
    args=["/Users/bytedance/Bowen_Yang_SWE/PRIVATE_WORKS/DeepRepo/mcp_system/servers/math_server.py"],
)


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)

            # Create and run the agent
            agent = create_react_agent("claude-3-5-sonnet-latest", tools)
            agent_response = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"})
            return agent_response

if __name__ == "__main__":
    import asyncio
    response = asyncio.run(run())
    print(response)
