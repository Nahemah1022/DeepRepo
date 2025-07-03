from typing import TypedDict
from langgraph.graph import StateGraph, END, START

class InputState(TypedDict):
    user_input: str

class OutputState(TypedDict):
    graph_output: str

class OverallState(TypedDict):
    foo: str
    user_input: str
    graph_output: str
    bowen: str

class PrivateState(TypedDict):
    bar: str


class PrivateState2(TypedDict):
    bar:str

# def node_4(state:)

# def node_4(state)

def node_1(state: InputState) -> OverallState:
    print(f"This is node 1 and state is {state}")
    return {"foo": state["user_input"] + " name"}

def node_2(state: OverallState) -> PrivateState:
    print(f"This is node 2 and state is {state}")
    return {"bar": state["foo"] + " is a pig"}


def node_3(state: OverallState) -> OutputState:
    print(f"This is node 3 and state is {state}")
    return {"graph_output": state["foo"] + " Lance"}


def node_4(state: PrivateState) -> OutputState:
    print(f"This is node 4 and state is {state}")
    return {"graph_output": state["bar"] + " Lance"}

def node_5(state: PrivateState) -> OutputState:
    print(f"This is node 5 and state is {state}")
    return {"graph_output": state["bar"] + " pp"}

def node_6(state:OutputState) -> OverallState:
    print(f"This is node 6 and state is {state}")
    return {"foo": "Overall fool"}



builder = StateGraph(OverallState)


builder.add_node("node_1",node_1 )
builder.add_node("node_2",node_2 )
# 添加边
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", END)


# 编译并运行
graph = builder.compile()
result = graph.invoke({"user_input": "My"})
print(result)  


"""
结果为
This is node 1 and state is {'user_input': 'My'}
This is node 2 and state is {'foo': 'My name', 'user_input': 'My'}
{'foo': 'My name', 'user_input': 'My'}

1. 明明最后node 2 输出为private state为什么结果没有bar在里面？
"""