from __future__ import annotations
from typing import TypedDict
from langgraph.graph import StateGraph, END
from shared import nodes

class WorkflowState(TypedDict, total=False):
    log: list
    category: str
    resolution: str
    _config: dict

intake = nodes.make_step("intake:accept", updates={"request_id":"R-001"}, event="done")
def classify(state, config):
    cat = config.get("category", "tech")
    nodes._ensure_log(state).append(f"classify:{cat}")
    state["category"]=cat
    ev = "route.billing" if cat=="billing" else "route.tech"
    return {"update": state, "events":[ev]}
billing_agent = nodes.make_step("agent:billing:resolve", updates={"resolution":"refund-policy"}, event="done")
tech_agent = nodes.make_step("agent:tech:diagnose", updates={"resolution":"restart-client"}, event="done")
compose_reply = nodes.make_step("reply:compose", event="done")

def build_app():
    wf = StateGraph(WorkflowState)
    wf.add_node("intake", lambda s: intake(s, s.get("_config", {}))["update"])
    wf.add_node("classify", lambda s: classify(s, s.get("_config", {}))["update"])
    wf.add_node("billing_agent", lambda s: billing_agent(s, s.get("_config", {}))["update"])
    wf.add_node("tech_agent", lambda s: tech_agent(s, s.get("_config", {}))["update"])
    wf.add_node("compose_reply", lambda s: compose_reply(s, s.get("_config", {}))["update"])

    wf.set_entry_point("intake")
    wf.add_edge("intake","classify")

    def route(s: WorkflowState):
        return "route.billing" if s.get("category")=="billing" else "route.tech"

    wf.add_conditional_edges("classify", route, {"route.billing":"billing_agent","route.tech":"tech_agent"})
    wf.add_edge("billing_agent","compose_reply")
    wf.add_edge("tech_agent","compose_reply")
    wf.add_edge("compose_reply", END)
    return wf.compile()
