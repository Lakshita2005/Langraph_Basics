from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class OrderState(TypedDict):
    item: str
    price: int
    tax: int
    total: int

def add_item(state: OrderState) -> dict:
    print(f"  [add_item]    reading: item={state['item']}")
    return {"price": 100}

def compute_tax(state: OrderState) -> dict:
    print(f"  [compute_tax] reading: price={state['price']}")
    tax = int(state["price"] * 0.18)
    return {"tax": tax}

def compute_total(state: OrderState) -> dict:
    print(f"  [compute_total] reading: price={state['price']}, tax={state['tax']}")
    return {"total": state["price"] + state["tax"]}

builder = StateGraph(OrderState)
builder.add_node("add_item", add_item)
builder.add_node("compute_tax", compute_tax)
builder.add_node("compute_total", compute_total)

builder.add_edge(START, "add_item")
builder.add_edge("add_item", "compute_tax")
builder.add_edge("compute_tax", "compute_total")
builder.add_edge("compute_total", END)

graph = builder.compile()
print("Running graph...")
result = graph.invoke({"item": "Notebook", "price": 0, "tax": 0, "total": 0})

# ----------------------- -----------------------
print("\n\nFinal state:", result,'\n\n')
print(graph.get_graph().draw_ascii())
print('\n\n')