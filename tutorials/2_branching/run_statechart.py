import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared.run_statechart import run
from shared import nodes

CONFIG = {"category": "tech"}
# CONFIG = {"category": "billing"}


intake = nodes.make_step("intake:accept", updates={"request_id": "R-001"}, event="done")

def classify(state, config):
    # имитируем классификацию; удобно управлять через config
    cat = config.get("category", "tech")
    nodes._ensure_log(state).append(f"classify:{cat}")
    state["category"]=cat
    ev = "route.billing" if cat=="billing" else "route.tech"
    return {"update": state, "events":[ev]}

billing_agent = nodes.make_step("agent:billing:resolve", updates={"resolution": "refund-policy"}, event="done")
tech_agent = nodes.make_step("agent:tech:diagnose", updates={"resolution": "restart-client"}, event="done")
compose_reply = nodes.make_step("reply:compose", event="done")

node_map = {"intake": intake,
            "classify": classify,
            "billing_agent": billing_agent,
            "tech_agent": tech_agent,
            "compose_reply": compose_reply}

run("diagram.scxml", node_map, initial_state={}, config=CONFIG, verbose=True)
