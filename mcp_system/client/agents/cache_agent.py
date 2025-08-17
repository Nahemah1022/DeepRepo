from agents.agent import Agent
from data_models.cache_agent_data_models import CacheAgentState, NodeInfo
from preprocess.preprocess import Preprocess
from typing import TypedDict, Dict
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

class CacheAgentNodes:
    """
    This class contains the logic for a LangGraph node that generates context 
    for a single code component (node).
    """
    def __init__(self, llm: ChatOpenAI, node_map: Dict[NodeInfo, CacheAgentState]):
        """
        Initializes the node logic handler.

        Args:
            llm: An initialized language model client (e.g., ChatOpenAI).
            node_map: A complete map where keys are NodeInfo objects and 
                      values are their corresponding CacheAgentState. This is
                      used to look up the context of dependencies.
        """
        self.llm = llm
        self.node_map = node_map

    def fill_context(self, target_state: CacheAgentState) -> CacheAgentState:
        """
        Generates a summary (context) for a given node, using the context
        of its dependencies to inform the result.

        Args:
            target_state: The CacheAgentState object for the node to be processed.

        Returns:
            An updated CacheAgentState object with the 'context' field filled.
        """
        print(f"--- Generating context for: {target_state.node.name} ---")

        # 1. Gather the contexts of all dependencies using the node_map
        dependency_contexts = []
        for dep_node_info in target_state.dependencies:
            # Look up the full state of the dependency
            if dep_node_info in self.node_map:
                dep_state = self.node_map[dep_node_info]
                if dep_state.context:
                    context_str = f"### Dependency Name: {dep_state.node.name}\n"
                    context_str += f"### Dependency Summary:\n{dep_state.context}\n"
                    dependency_contexts.append(context_str)
            else:
                # This case should ideally not happen if the graph is complete
                print(f"Warning: Could not find state for dependency {dep_node_info.name}")

        # 2. Construct the prompt for the language model
        system_message = SystemMessage(
            content="You are an expert programmer tasked with creating a concise, high-level summary of a code component. "
                    "Your summary should explain the component's primary purpose and how it uses its dependencies. "
                    "Focus on the 'what' and 'why', not a line-by-line explanation of the 'how'."
        )

        prompt_template = f"""Your task is to summarize the following code component:
                            ## Component Name: {target_state.node.name}
                            ## Component Type: {target_state.node.type}
                            ## Component Code:
                            {target_state.node.code_content}
                            """
        if dependency_contexts:
            prompt_template += """
                                \n--- ## Dependencies Information --
                                To help you, here are the summaries of the components it directly depends on. Your summary MUST explain how the main code component uses these dependencies.
                                
                                """
            prompt_template += "\n".join(dependency_contexts)
        else:
            prompt_template += "\nThis component has no dependencies."
        prompt_template += "\n---\n## Your Task\nBased on all the information above, provide a concise summary for the main component. "
        prompt_template += "Do not include the component name or headers in your response. Provide only the summary text."

        human_message = HumanMessage(content=prompt_template)
    
        response = self.llm.invoke([system_message, human_message])
        generated_context = response.content
        
        # For demonstration, we'll use a placeholder context.

        generated_context = f"This is a generated summary for the '{target_state.node.type}' named '{target_state.node.name}'."
        if dependency_contexts:
            generated_context += f" It utilizes its {len(dependency_contexts)} dependencies to perform its function."
        generated_context += response.content


        # 4. Return an updated copy of the state
        # Using dataclasses.replace is a clean way to create a new, updated instance.
        self.node_map[target_state.node].context = generated_context
            
        return self.node_map[target_state.node]
    

class CacheAgent(Agent):
    def __init__(self, preprocess:Preprocess):
        super().__init__(preprocess=preprocess, overall_state=CacheAgentState)
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        self.cache_agent_nodes = CacheAgentNodes(llm=self.llm, node_map=self.preprocess.get_graph())
        self.build_agent()

    def build_agent(self):
        self.builder.add_node("fill_context",self.cache_agent_nodes.fill_context)
        self.builder.add_edge(START, "fill_context")
        self.builder.add_edge("fill_context", END)
        self.agent = self.builder.compile()
        
    
    def start(self):
        for data in self.preprocess.get_data():
            self.agent.invoke(data)
        self.preprocess.store_data()

        