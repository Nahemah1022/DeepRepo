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

# 添加节点
# builder.add_node("node_1", node_1)
# builder.add_node("node_2", node_2)
# builder.add_node("node_3", node_3)
builder.add_node("node_1",node_1 )
builder.add_node("node_2",node_2 )
builder.add_node("node_3",node_3 )
builder.add_node("node_4",node_4 )
builder.add_node("node_5",node_5 )
builder.add_node("node_6",node_6 )
# 添加边
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_1", "node_3")
builder.add_edge("node_3", "node_4")
builder.add_edge("node_5", "node_6")
builder.add_edge("node_6", END)

# # ✅ 设置入口和出口 schema
# builder.set_entry_point("node_1", schema=InputState)
# builder.set_finish_point("node_3", schema=OutputState)

# 编译并运行
graph = builder.compile()
result = graph.invoke({"user_input": "My"})
print(result)  # {'graph_output': 'My name is Lance'}


"""
结果为
This is node 1 and state is {'user_input': 'My'}
This is node 2 and state is {'foo': 'My name', 'user_input': 'My'}
This is node 3 and state is {'foo': 'My name', 'user_input': 'My'}
This is node 4 and state is {'bar': 'My name is a pig'}
{'foo': 'My name', 'user_input': 'My', 'graph_output': 'My name is a pig Lance'}

1. 这里明明node 4 的input type和3的ouput type完全不同，但还是有这个值。
2. 如果 comment掉node1和node2的那条edge，2不会自动触发，就导致黑板里没这个值，然后处理到node_3到node_4就会报错
3. node_6虽然有通过add edge注册，并且接受值OutputState的graph_output但是由于node 5 不在逻辑链路上没有触发，node 6也没有触发。说明node触发逻辑与state中的值变化节藕，没有任何关系

总结：
所以每次传入的值都是黑板里的所有变量，然后input的parameter只是一个筛选器，从黑板取一个subset传入。和上一个node是谁，产出什么结果没关系
add edge是做什么的？只是用来做好graph用的，看起来langgraph并不是事件驱动，并不是根据某种特定数启动就启动， 
node触发逻辑与state中的值变化节藕，没有任何关系
"""