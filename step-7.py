from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

# Same human-in-the-loop graph as step-7, but this time the pause AND the resume
# happen in ONE process. That's why InMemorySaver is fine here: the checkpoint
# only has to survive between two calls in the same running script, not between
# two separate `python3 ...` invocations (which is what step-7 needed sqlite for).


class State(TypedDict):
    input: str
    approved: bool
    result: str


def prepare_action(state: State):
    print(f"Preparing action for input: {state['input']}")
    return {"input": state["input"]}


def human_review(state: State):
    # Pauses execution here and surfaces this payload to whoever is running the graph
    decision = interrupt(
        {
            "question": "Approve this action?",
            "action_preview": f"About to process: {state['input']}",
        }
    )
    # Execution resumes here once Command(resume=...) is sent back in
    return {"approved": decision.get("approved", False)}


def execute_action(state: State):
    if state["approved"]:
        return {"result": f"Executed: {state['input']}"}
    return {"result": "Action rejected by human"}


def route_after_review(state: State):
    return "execute_action" if state["approved"] else END


graph = StateGraph(State)
graph.add_node("prepare_action", prepare_action)
graph.add_node("human_review", human_review)
graph.add_node("execute_action", execute_action)

graph.add_edge(START, "prepare_action")
graph.add_edge("prepare_action", "human_review")
graph.add_conditional_edges("human_review", route_after_review, {"execute_action": "execute_action", END: END})
graph.add_edge("execute_action", END)

checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)

# --- Running it, all in one process ---
config = {"configurable": {"thread_id": "thread-1"}}

# 1) First run — pauses at human_review. The returned state carries an
#    "__interrupt__" key describing what the graph is waiting on.
paused = app.invoke({"input": "delete all logs older than 30 days"}, config=config)
print("\nPaused. The graph is asking:")
for intr in paused["__interrupt__"]:
    print("  ", intr.value)

# 2) Ask the actual human at the terminal. Their y/n answer becomes the value
#    that `interrupt(...)` returns inside human_review when we resume.
answer = input("Approve this action? [y/n]: ").strip().lower()
approved = answer in ("y", "yes")

# 3) Resume the paused graph with the human's decision. Same process, same
#    checkpointer, so the paused state is still in memory and ready to go.
final_result = app.invoke(Command(resume={"approved": approved}), config=config)

# ----------------------- -----------------------
print("\n\nFinal state:", final_result, '\n\n')