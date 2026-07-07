from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class ExamState(TypedDict):
    score: int
    result: str

def check_score(state: ExamState) -> dict:
    print(f"  [check_score] score={state['score']}")
    return {}

def route_by_score(state: ExamState) -> str:
    if state["score"] >= 40:
        return "pa"
    else:
        return "fn"

def pass_node(state: ExamState) -> dict:
    return {"result": "PASSED"}

def fail_node(state: ExamState) -> dict:
    return {"result": "FAILED - needs re-exam"}

builder = StateGraph(ExamState)
builder.add_node("check_score", check_score)
builder.add_node("pass_node", pass_node)
builder.add_node("fail_node", fail_node)

builder.add_edge(START, "check_score")
builder.add_conditional_edges(
    "check_score", #this is the node you are currently executing
    route_by_score, # this is the router that decides where to go
    {"pa": "pass_node", "fn": "fail_node"} # mapping so you can return
    #arbritrary naming convention
)
builder.add_edge("pass_node", END)
builder.add_edge("fail_node", END)

graph = builder.compile()

for s in [72, 25]:
    print(f"\nStudent scored {s}:")
    print(" ->", graph.invoke({"score": s, "result": ""}), '\n')


# ----------------------- -----------------------
print('\n\n')
print(graph.get_graph().draw_ascii())
print('\n\n')