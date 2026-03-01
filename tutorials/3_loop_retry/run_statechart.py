import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared.run_statechart import run
from shared import nodes

CONFIG = {"success_rate": 0.45, # Вероятность успешной оплаты (используется для симуляции), 0.0 - всегда неудачная оплата, 1.0 - всегда удачная оплата
          "max_attempts": 3}    # Количество попыток автоматической оплаты заказа

prepare = nodes.make_step("payment:prepare", updates={"amount": 42.0}, event="done")

def charge(state, config):
    import random
    nodes._ensure_log(state).append("payment:charge_attempt")
    state["attempts"] = state.get("attempts", 0) + 1
    ok = random.random() < config["success_rate"]
    state["charge_ok"] = ok
    return {"update": state, "events": ["pay.ok" if ok else "pay.fail"]}

wait = nodes.make_step("payment:backoff_wait", event="tick")
manual = nodes.make_step("payment:manual_review", updates={"status":"manual"}, event="done")
receipt = nodes.make_step("payment:receipt_issued", updates={"status":"paid"}, event="done")

node_map={"prepare": prepare,
          "charge": charge,
          "wait": wait,
          "manual": manual,
          "receipt":receipt}

run("diagram.scxml", node_map, initial_state={}, config=CONFIG, verbose=True)
