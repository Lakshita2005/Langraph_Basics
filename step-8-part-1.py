from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt, Command

# Persistent checkpoint file on disk. InMemorySaver would NOT work here:
# it only lives inside one Python process, so the paused state would vanish
# the moment this script exits. Writing to sqlite lets step-7-part-2.py
# (a separate process) pick the pause back up and resume it.
DB_PATH = "step-8-part-1-checkpoints.sqlite"


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

# --- Running it ---
# SqliteSaver.from_conn_string is a context manager; the connection closes when
# the `with` block exits, but the checkpoint stays saved in the file on disk.
with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
    app = graph.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-1"}}

    # First run — will pause at human_review
    result = app.invoke({"input": "delete all logs older than 30 days"}, config=config)

    # ----------------------- -----------------------
    print("\n\nPaused, waiting for human review.\n\n")
    print("State so far:\n")
    print(result, '\n\n')