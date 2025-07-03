# Create server parameters for stdio connection
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
load_dotenv()

server_params = StdioServerParameters(
    command="python",
    # Make sure to update to the full absolute path to your math_server.py file
    args=["/Users/bytedance/Bowen_Yang_SWE/PRIVATE_WORKS/DeepRepo/mcp_system/servers/math_server.py"],
)

# No need to stream, this stream is each token appear
async def iter_run_finished(agent, config, message):
    async for stream_mode, chunk in agent.astream(
    message,
    config=config,
    stream_mode=["updates", "messages", "custom"]
    ):
        print("CHUNK IS ", chunk)
        print("\n")
        print("STREAM_MODE is ", stream_mode)
    


async def run():
    checkpointer = InMemorySaver()
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)

            # Create and run the agent
            agent = create_react_agent("claude-3-5-sonnet-latest", 
                                       tools=tools,
                                       checkpointer=checkpointer)
            config = {
                "configurable": {
                    "thread_id": "1"  
                }
            }
            # message1 = {"messages": "what's (3 + 5) x 12?"}
            # message2 = {"messages":"What is last round quest and answer?"}
            agent_response = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"}, config=config)
            print("FIRST ROUND --------",agent_response)
            # await iter_run_finished(agent=agent,config=config, message=message1)
            # agent_response = await agent.ainvoke({"messages":"What is last round quest and answer?"}, config=config)
            # print("SECOND ROUND --------")
            # await iter_run_finished(agent=agent,config=config, message=message2)
            return

if __name__ == "__main__":
    import asyncio
    response = asyncio.run(run())
    print(response)
