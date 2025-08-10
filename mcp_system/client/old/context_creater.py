import operator
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# --- 1. Define the State and Model (Same as before) ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# Ensure your API key is set
# os.environ["OPENAI_API_KEY"] = "your_api_key_here" 
model = ChatOpenAI(temperature=0)

# --- 2. Define the Nodes ---

def build_prompt_node(state: AgentState):
    """
    Pre-builds a prompt and adds it to the message history.
    This node doesn't call the LLM.
    """
    print("---CALLING PROMPT BUILDER NODE---")
    
    # Create a new, specific message to guide the next step.
    # This message is "hardcoded" for this example.
    instruction = HumanMessage(
        content="Based on our conversation, please summarize the key points in three bullets."
    )
    instruction = SystemMessage(
        content=[]
    )
    
    # Return the new message to be added to the state.
    return {"messages": [instruction]}

def agent_node(state: AgentState):
    """
    Invokes the LLM with the full, updated message history.
    """
    print("---CALLING AGENT NODE---")
    
    # The 'messages' in the state now include the pre-built instruction
    messages = state['messages']
    
    response = model.invoke(messages)
    
    return {"messages": [response]}