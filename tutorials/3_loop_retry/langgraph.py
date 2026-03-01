from __future__ import annotations
from typing import TypedDict
from langgraph.graph import StateGraph, END
from shared import nodes
import random

class WorkflowState(TypedDict, total=False):
    log: list
    attempts: int
    status: str
    _config: dict

prepare = nodes.make_step("payment:prepare", updates={"amount":42.0}, event="done")
wait = nodes.make_step("payment:backoff_wait", event="tick")
manual = nodes.make_step("payment:manual_review", updates={"status":"manual"}, event="done")
receipt = nodes.make_step("payment:receipt_issued", updates={"status":"paid"}, event="done")

def charge_step(s, cfg):
    nodes._ensure_log(s).append("payment:charge_attempt")
    s["attempts"]=s.get("attempts",0)+1
    sr=float(cfg.get("success_rate", 0.45))
    ok = random.random() < sr
    s["charge_ok"]=ok
    return s

def build_app():
    wf = StateGraph(WorkflowState)
    wf.add_node("prepare", lambda s: prepare(s, s.get("_config", {}))["update"])
    wf.add_node("charge", lambda s: charge_step(s, s.get("_config", {})))
    wf.add_node("wait", lambda s: wait(s, s.get("_config", {}))["update"])
    wf.add_node("manual", lambda s: manual(s, s.get("_config", {}))["update"])
    wf.add_node("receipt", lambda s: receipt(s, s.get("_config", {}))["update"])

    wf.set_entry_point("prepare")
    wf.add_edge("prepare","charge")

    def route_after_charge(s: WorkflowState):
        return "ok" if s.get("charge_ok") else "fail"
    wf.add_conditional_edges("charge", route_after_charge, {"ok":"receipt","fail":"wait"})

    def route_after_wait(s: WorkflowState):
        maxa=int(s.get("_config", {}).get("max_attempts",3))
        return "manual" if s.get("attempts",0) >= maxa else "retry"
    wf.add_conditional_edges("wait", route_after_wait, {"retry":"charge","manual":"manual"})
    
    wf.add_edge("manual", END)
    wf.add_edge("receipt", END)
    return wf.compile()
