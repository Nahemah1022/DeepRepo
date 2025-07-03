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

# def node_1(state: InputState) -> OverallState:
#     return {"foo": state["user_input"] + " name"}

# def node_2(state: OverallState) -> PrivateState:
#     return {"bar": state["foo"] + " is"}

# def node_3(state: PrivateState) -> OutputState:
#     return {"graph_output": state["bar"] + " Lance"}


def node_parralell_test_0(state:InputState)->PrivateState:
    return {"bar": state["user_input"]}

def node_parralell_test_1(state: PrivateState) -> OverallState:
    return {"foo": state["bar"] + " name"}

def node_parralell_test_2(state:PrivateState) -> OverallState:
    return {"bowen": state["bar"] + " name"}
# ✅ 初始化时只传 OverallState
builder = StateGraph(OverallState)

# 添加节点
# builder.add_node("node_1", node_1)
# builder.add_node("node_2", node_2)
# builder.add_node("node_3", node_3)
builder.add_node("node_1",node_parralell_test_0 )
builder.add_node("node_2",node_parralell_test_1 )
builder.add_node("node_3",node_parralell_test_2 )
# 添加边
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
# builder.add_edge("node_2", "node_3")
builder.add_edge("node_2", END)

# # ✅ 设置入口和出口 schema
# builder.set_entry_point("node_1", schema=InputState)
# builder.set_finish_point("node_3", schema=OutputState)

# 编译并运行
graph = builder.compile()
result = graph.invoke({"user_input": "My"})
print(result)  # {'graph_output': 'My name is Lance'}


# TODO: 希望能够看到每一步所有state的变化