from __future__ import annotations
from typing import TypedDict
from langgraph.graph import StateGraph, END
from shared import nodes

class WorkflowState(TypedDict, total=False):
    log: list
    sources: list
    results: list
    pending: int
    success: int
    fail: int
    finalized: bool
    _config: dict

def _node(node_fn):
    """Преобразует контракт узла {update, events} в обновление состояния для LangGraph."""
    def wrapper(s: dict) -> dict:
        res = node_fn(s, s.get("_config", {}))
        if isinstance(res, dict) and "update" in res:
            return res["update"]
        return res if isinstance(res, dict) else {}
    return wrapper

def build_app():
    wf = StateGraph(WorkflowState)

    wf.add_node("initialize", _node(nodes.initialize))
    wf.add_node("search", _node(nodes.search))
    wf.add_node("finalize", _node(nodes.finalize))

    wf.set_entry_point("initialize")

    wf.add_edge("initialize", "search")
    wf.add_edge("search", "finalize")
    wf.add_edge("finalize", END)

    return wf.compile()
