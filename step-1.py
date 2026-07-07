from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    message: str

def greet(state: State) -> dict:
    return{"message": state["message"] + " -> greeted by node!"}

builder = StateGraph(State)
builder.add_node("greet",greet)
builder.add_edge(START,"greet")
builder.add_edge("greet",END)

graph = builder.compile()
result = graph.invoke({"message":"hello"})

# ---------------
print('\n\n',result,'\n\n')
print(graph.get_graph().draw_ascii())
print('\n\n')
print(graph.get_graph().draw_ascii())