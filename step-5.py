from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import random

class GuessState(TypedDict):
    target: int
    guess: int
    attempts: int

def make_guess(state: GuessState) -> dict:
    guess = random.randint(1, 20)
    print(f"  attempt {state['attempts']+1}: guessing {guess}")
    return {"guess": guess, "attempts": state["attempts"] + 1}

def is_correct(state: GuessState) -> str:
    if state["guess"] == state["target"]:
        return "done"
    if state["attempts"] >= 10:
        return "give_up"
    return "retry"

builder = StateGraph(GuessState)
builder.add_node("make_guess", make_guess)
builder.add_edge(START, "make_guess")
builder.add_conditional_edges(
    "make_guess",
    is_correct,
    {"done": END, "give_up": END, "retry": "make_guess"}   # <- loop: points back to itself
)

graph = builder.compile()
result = graph.invoke({"target": 7, "guess": 0, "attempts": 0})


# ----------------------- -----------------------
print("\n\nFinal state:", result,'\n\n')
print(graph.get_graph().draw_mermaid())
print('\n\n')