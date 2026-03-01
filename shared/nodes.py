"""
Общие узлы для примеров.

Контракт узла:
- вход: state (dict), config (dict)
- выход: dict с ключами:
  - update: dict (патч состояния)
  - events: list[str] (события для оркестрации)
"""
from __future__ import annotations
from typing import Any, Dict, List
import random
import time

def initialize(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    return {"update": {"log": []}, "events": ["done"]}

def search(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    sources = list(config.get("sources", ["s1","s2","s3"]))
    return {"update": {"sources": sources, "results": [], "pending": len(sources), "success": 0, "fail": 0}, "events": ["done"]}

def analyze_one(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    # имитация анализа 1 источника (один вызов = один источник)
    if not state.get("sources"):
        return {"events": ["queue.empty"]}
    src = state["sources"].pop(0)
    ok = random.random() >= config.get("fail_rate", 0.2)
    state["results"].append({"src": src, "ok": ok})
    state["pending"] = max(0, state.get("pending", 0) - 1)
    state["success"] = state.get("success", 0) + (1 if ok else 0)
    state["fail"] = state.get("fail", 0) + (0 if ok else 1)
    return {"update": state, "events": ["check.ok" if ok else "check.fail"]}

def finalize(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    state["finalized"] = True
    return {"update": state, "events": ["done"]}

def quality_check(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    # простая проверка: успех если ошибок нет
    ok = state.get("fail", 0) == 0
    state["quality_ok"] = ok
    return {"update": state, "events": ["done"]}

# --- специальные узлы для усиленных примеров ---

def create_resource(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    # создаём внешний ресурс
    rid = f"res_{int(time.time()*1000)}"
    state["resource_id"] = rid
    state["resource_created"] = True
    return {"update": state, "events": ["resource.created"]}

def do_work_after_create(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    # может упасть "после" внешнего эффекта
    if random.random() < config.get("work_fail_rate", 0.5):
        state["work_failed"] = True
        return {"update": state, "events": ["work.fail"]}
    state["work_failed"] = False
    return {"update": state, "events": ["work.ok"]}

def compensate(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    # имитация компенсации, может падать
    state["comp_attempts"] = state.get("comp_attempts", 0) + 1
    if state.get("compensated"):
        return {"update": state, "events": ["comp.ok"]}
    if not state.get("resource_id"):
        state["compensated"] = True
        return {"update": state, "events": ["comp.ok"]}
    ok = random.random() >= config.get("comp_fail_rate", 0.4)
    if ok:
        state["compensated"] = True
        return {"update": state, "events": ["comp.ok"]}
    return {"update": state, "events": ["comp.fail"]}

def emit_done(state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    return {"events": ["done"]}
