from __future__ import annotations
import importlib.util, os, sys
from typing import Any, Dict

def load_app(langgraph_py_path: str):
    spec = importlib.util.spec_from_file_location("example_langgraph", langgraph_py_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.build_app()

def run(langgraph_py_path: str, initial_state: Dict[str, Any]|None=None, config: Dict[str, Any]|None=None, verbose: bool = False):
    app = load_app(langgraph_py_path)
    # Передаём config в state; узлы читают его как state["_config"] (как в statechart)
    state = dict(initial_state or {})
    if config:
        state["_config"] = config
    if verbose:
        step = 0
        out = state
        for chunk in app.stream(state, stream_mode="values"):
            step += 1
            print(f"[шаг {step}] state={chunk}")
            out = chunk
    else:
        out = app.invoke(state)
    print("Финальное состояние:", out)
