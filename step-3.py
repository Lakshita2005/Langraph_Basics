from typing_extensions import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END

class LogState(TypedDict):
    steps: Annotated[list[str], add]   # <- the reducer: HOW to combine old + new

def step_a(state: LogState) -> dict:
    return {"steps": ["step_a ran"]}   # this gets ADDED to the list, not replacing it

def step_b(state: LogState) -> dict:
    return {"steps": ["step_b ran"]}

def step_c(state: LogState) -> dict:
    return {"steps": ["step_c ran"]}

builder = StateGraph(LogState)
builder.add_node("step_a", step_a)
builder.add_node("step_b", step_b)
builder.add_node("step_c", step_c)
builder.add_edge(START, "step_a")
builder.add_edge("step_a", "step_b")
builder.add_edge("step_b", "step_c")
builder.add_edge("step_c", END)

graph = builder.compile()
result = graph.invoke({"steps": []})

# ----------------------- -----------------------
print("\n\nFinal state:", result,'\n\n')
print(graph.get_graph().draw_ascii())
print('\n\n')