from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from IPython.display import Image, display

class ChatState(TypedDict):
    turns: int

def bump(state: ChatState) -> dict:
    # print(f"current turn : {state.get("turns")}")
    return {"turns": state.get("turns", 0) + 1}

builder = StateGraph(ChatState)
builder.add_node("bump", bump)
builder.add_edge(START, "bump")
builder.add_edge("bump", END)

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "student-1"}}

print("call 1:", graph.invoke({"turns": 0}, config))
print("call 2:", graph.invoke({}, config))   # empty input -> reuses saved state
print("call 3:", graph.invoke({}, config))

config2 = {"configurable": {"thread_id": "student-2"}}
print("student-2 (fresh thread):", graph.invoke({"turns": 0}, config2))

# ----------------------- -----------------------
print('\n\n')
print(graph.get_graph().draw_ascii())
print('\n\n')