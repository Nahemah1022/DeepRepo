# First, ensure you have the necessary packages installed:
# pip install langgraph langchain langchain_openai duckduckgo-search

import os
import json
from typing import TypedDict, Annotated, Sequence, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from duckduckgo_search import DDGS
import operator
from dotenv import load_dotenv
load_dotenv()
# --- 1. Set up Environment and Tools ---

# Set your OpenAI API key
# For this example, you can set it as an environment variable
# os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY"

def duckduckgo_search_func(query: str) -> str:
    """
    A wrapper function to use the duckduckgo_search library for a text search.
    It takes a query, performs a search, and returns the results as a JSON string.
    """
    try:
        with DDGS() as ddgs:
            # We use the .text() method which returns a generator, and we'll take the first 5 results.
            results = [r for r in ddgs.text(query, max_results=5)]
            return json.dumps(results) if results else "No results found for the query."
    except Exception as e:
        return f"An error occurred during the search: {e}"

# Define a simple search tool for the agent to use, now with our updated function
search_tool = Tool(
    name="search_tool",
    func=duckduckgo_search_func,
    description="Useful for when you need to answer questions about current events, people, or places. Returns a JSON string of search results. Input should be a clear search query.",
)
tools = [search_tool]

# --- 2. Define the Agent's State ---

# The state is the memory of our graph. It's what gets passed between nodes.
# We use `operator.add` to specify that new messages should be appended to the
# existing list, rather than replacing it.
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# --- 3. Define the Graph Nodes ---

# The nodes are the fundamental processing units of the graph.
# Each node is a function that takes the current state and returns an update.

def should_continue(state: AgentState) -> str:
    """
    This is our conditional edge. It determines the next step based on the
    last message from the agent.

    - If the agent called a tool, we route to the 'action' node.
    - Otherwise, we have a final answer, so we 'end' the process.
    """
    print("---DECIDING NEXT STEP---")
    last_message = state['messages'][-1]
    # If the LLM made a tool call, then we need to execute it
    if last_message.tool_calls:
        print("Decision: Agent wants to use a tool. Routing to 'action'.")
        return "action"
    # Otherwise, we have a final answer
    print("Decision: Agent has a final answer. Ending.")
    return "end"

def call_model(state: AgentState) -> dict:
    """
    This is the "think" node. It invokes the LLM to decide what to do next.
    The LLM's response (which could be a tool call or a final answer) is
    added to the state.
    """
    print("---CALLING MODEL (THINKING)---")
    # We are using a ChatOpenAI model with tool-calling support
    model = ChatOpenAI(model="gpt-4-turbo", temperature=0)
    # Bind the tools to the model so it knows what it can do
    model_with_tools = model.bind_tools(tools)
    # Invoke the model with the current conversation history
    response = model_with_tools.invoke(state['messages'])
    # We return a dictionary with the new message to be added to the state
    return {"messages": [response]}

def call_tool(state: AgentState) -> dict:
    """
    This is the "act" node. It executes the tool that the agent decided to use.
    The output of the tool is then formatted as a ToolMessage and added to the state.
    """
    print("---EXECUTING TOOL (ACTING)---")
    last_message = state['messages'][-1]  # This will be the AIMessage with tool_calls

    # We can handle multiple tool calls in a single turn
    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call['name']
        print(f"Executing tool: '{tool_name}' with args: {tool_call['args']}")
        # Find the correct tool to execute
        tool_to_call = next(t for t in tools if t.name == tool_name)
        # Invoke the tool and get the result
        observation = tool_to_call.invoke(tool_call['args'])
        # We create a ToolMessage to represent the tool's output
        tool_messages.append(
            ToolMessage(content=str(observation), tool_call_id=tool_call['id'])
        )

    # We return a dictionary with the tool's output messages to be added to the state
    return {"messages": tool_messages}


# --- 4. Construct the Graph ---

from langgraph.graph import StateGraph, END

# Initialize a new state graph with our defined AgentState
workflow = StateGraph(AgentState)

# Add the nodes to the graph. These are the steps the agent can take.
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)

# Set the entry point for the graph. The first node to be called is 'agent'.
workflow.set_entry_point("agent")

# Add the conditional edge. This controls the flow of the graph.
# Based on the output of the 'agent' node, the graph will either
# route to the 'action' node or to the special 'END' node.
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "action": "action", # If the agent should continue, go to the action node
        "end": END,         # If the agent is done, end the graph
    },
)

# Add a normal edge from the 'action' node back to the 'agent' node.
# This creates the loop, allowing the agent to think again after acting.
workflow.add_edge("action", "agent")

# Compile the graph into a runnable object.
app = workflow.compile()


# --- 5. Run the Agent ---

# Now, let's interact with our agent.
# We'll start with a user question.
initial_input = "Who is the current CEO of OpenAI and what were the main products released under their leadership?"

# We invoke the graph using `stream` to see the output of each step.
# The input is a dictionary where the key 'messages' matches our AgentState.
inputs = {"messages": [HumanMessage(content=initial_input)]}

print(f"--- STARTING AGENT RUN for: '{initial_input}' ---\n")
for output in app.stream(inputs, stream_mode="values"):
    # The `stream` method yields the state after each step.
    # We can print the last message to see the agent's progress.
    last_message = output["messages"][-1]
    print("\n--- AGENT STEP ---")
    last_message.pretty_print()

print("\n--- AGENT RUN COMPLETE ---")
