from __future__ import annotations
from typing import Any, Dict
from statechart_engine import load_scxml, Engine
from . import nodes as shared_nodes

def run(scxml_path: str, node_map: Dict[str, Any], initial_state: Dict[str, Any]|None=None, config: Dict[str, Any]|None=None, verbose: bool=False):
    model = load_scxml(scxml_path)
    eng = Engine(model, nodes=node_map, config=config or {}, verbose=verbose)
    out = eng.run(initial_state=initial_state or {}, start_event="start")
    print("Финальное состояние:", out)
