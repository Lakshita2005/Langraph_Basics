from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt, Command

# Same checkpoint file step-7.py wrote to. This is how a *separate* process
# reloads the paused graph and resumes it.
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

# -----------------------------------------------------------------
# ... later, after a human looks at it and approves ...
# Re-open the same sqlite checkpoint file so the pause left by step-7.py is
# available on this thread_id. Run step-7.py FIRST, or there is nothing to resume.
with SqliteSaver.from_conn_string(DB_PATH) as checkpointer:
    app = graph.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "thread-1"}}

    # Read the interrupt that part-1 left in the checkpoint so the human can see
    # what they're approving. .interrupts holds the payload passed to interrupt(...).
    snapshot = app.get_state(config)
    if not snapshot.interrupts:
        print("Nothing is paused on this thread. Run step-8-part-1.py first.")
        raise SystemExit(0)

    pending = snapshot.interrupts[0].value
    print("\nThe graph is asking:")
    print("  ", pending["question"])
    print("  ", pending["action_preview"], "\n")

    # Ask the actual human at the terminal. Their y/n answer becomes the value
    # that interrupt(...) returns inside human_review when the graph resumes.
    answer = input("Approve this action? [y/n]: ").strip().lower()
    approved = answer in ("y", "yes")

    final_result = app.invoke(Command(resume={"approved": approved}), config=config)
    print("\nResumed and finished. Final state:", final_result, '\n')