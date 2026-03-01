"""
Минимальный исполнитель SCXML-подмножества для учебных примеров.

Поддержано:
- <scxml initial="...">
- <state id="..." node="..."> ... </state>
- <final id="..."/>
- <transition event="..." target="..."/>  (event optional)
- <transition cond="..."/>               (cond выражение на Python над state)
- <parallel> с дочерними <state>         (барьер: выход из parallel когда все ветки дошли до final)
- <history id="..." type="deep"/>        (упрощённо: запоминаем последний активный leaf в пределах родителя)
- <script> внутри transition             (выполняется в контексте state dict)

Важно: это не полнофункциональный SCXML-runtime; цель — показать различия формализма управления.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET
import time

NodeFn = Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]

@dataclass
class Transition:
    event: Optional[str]
    cond: Optional[str]
    target: str
    script: Optional[str]

@dataclass
class StateDef:
    id: str
    node: Optional[str]
    transitions: List[Transition]
    children: List[str]
    is_parallel: bool = False
    is_final: bool = False
    is_history: bool = False
    history_type: str = "deep"
    parent: Optional[str] = None

class SCXMLModel:
    def __init__(self, initial: str, states: Dict[str, StateDef], root_id: str="__root__"):
        self.initial = initial
        self.states = states
        self.root_id = root_id

def _strip_ns(tag: str) -> str:
    return tag.split("}",1)[-1] if "}" in tag else tag

def load_scxml(path: str) -> SCXMLModel:
    tree = ET.parse(path)
    root = tree.getroot()
    if _strip_ns(root.tag) != "scxml":
        raise ValueError("Ожидался корневой <scxml>")

    initial = root.attrib.get("initial")
    if not initial:
        raise ValueError("В <scxml> должен быть initial")

    states: Dict[str, StateDef] = {}

    # создаём виртуальный root, чтобы упростить глобальные переходы
    states["__root__"] = StateDef(id="__root__", node=None, transitions=[], children=[], parent=None)

    def parse_state(elem: ET.Element, parent: str) -> str:
        tag = _strip_ns(elem.tag)
        if tag == "final":
            sid = elem.attrib["id"]
            states[sid] = StateDef(id=sid, node=None, transitions=[], children=[], is_final=True, parent=parent)
            states[parent].children.append(sid)
            return sid

        if tag == "history":
            sid = elem.attrib["id"]
            htype = elem.attrib.get("type","deep")
            states[sid] = StateDef(id=sid, node=None, transitions=[], children=[], is_history=True, history_type=htype, parent=parent)
            states[parent].children.append(sid)
            return sid

        if tag != "state":
            raise ValueError(f"Неподдерживаемый элемент: {tag}")

        sid = elem.attrib["id"]
        node = elem.attrib.get("node")
        sdef = StateDef(id=sid, node=node, transitions=[], children=[], parent=parent)
        states[sid] = sdef
        states[parent].children.append(sid)

        # transitions
        for ch in list(elem):
            ctag = _strip_ns(ch.tag)
            if ctag == "transition":
                ev = ch.attrib.get("event")
                cond = ch.attrib.get("cond")
                target = ch.attrib.get("target")
                if not target:
                    raise ValueError(f"<transition> в {sid} без target")
                script = None
                for sub in list(ch):
                    if _strip_ns(sub.tag) == "script":
                        script = (sub.text or "").strip()
                sdef.transitions.append(Transition(event=ev, cond=cond, target=target, script=script))
            elif ctag == "parallel":
                # параллель: делаем отдельное состояние-супервизор, children внутри
                sdef.is_parallel = True
                for st in list(ch):
                    parse_state(st, sid)
            elif ctag in ("state","final","history"):
                parse_state(ch, sid)
            elif ctag in ("onentry","onexit","datamodel","data","metadata"):
                # пропускаем: для учебных примеров node запускаем по атрибуту state@node
                continue
            else:
                # мягко игнорируем прочее
                continue
        return sid

    # парсим дочерние states на верхнем уровне
    for child in list(root):
        ctag = _strip_ns(child.tag)
        if ctag in ("state","final","history"):
            parse_state(child, "__root__")
        elif ctag == "transition":
            # глобальные transition на root scxml
            ev = child.attrib.get("event")
            cond = child.attrib.get("cond")
            target = child.attrib.get("target")
            script = None
            for sub in list(child):
                if _strip_ns(sub.tag) == "script":
                    script = (sub.text or "").strip()
            states["__root__"].transitions.append(Transition(ev, cond, target, script))
        else:
            continue

    return SCXMLModel(initial=initial, states=states, root_id="__root__")

class Engine:
    def __init__(self, model: SCXMLModel, nodes: Dict[str, NodeFn], config: Optional[Dict[str, Any]]=None, verbose: bool=False):
        self.model = model
        self.nodes = nodes
        self.config = config or {}
        self.verbose = verbose
        self.state: Dict[str, Any] = {}
        self.event_queue: List[str] = []
        self.active: List[str] = []  # листовые активные состояния
        self.history: Dict[str, str] = {}  # parent -> last leaf

    def send(self, event: str) -> None:
        self.event_queue.append(event)

    def _eval_cond(self, cond: str) -> bool:
        # безопасное подмножество: только state и config
        env = {"state": self.state, "config": self.config}
        return bool(eval(cond, {"__builtins__": {}}, env))

    def _run_script(self, script: str) -> None:
        env = {"state": self.state, "config": self.config}
        exec(script, {"__builtins__": {}}, env)

    def _enter_leaf(self, sid: str) -> None:
        sdef = self.model.states[sid]
        if sdef.is_final:
            self.active.append(sid)
            return

        if sdef.is_history:
            # history leaf — перейти в сохранённый leaf родителя
            parent = sdef.parent
            if not parent:
                raise ValueError("History без parent")
            target = self.history.get(parent)
            if not target:
                # если нет истории — войти в первого ребёнка родителя
                target = self.model.states[parent].children[0]
            self._enter_leaf(target)
            return

        if sdef.is_parallel:
            # активируем по одному leaf в каждом дочернем state (берём их initial = первый ребёнок)
            for child in sdef.children:
                self._enter_leaf(child)
            return

        # обычное состояние: если есть дети — войти в первого ребёнка, иначе leaf
        if sdef.children:
            self._enter_leaf(sdef.children[0])
            return

        # leaf
        self.active.append(sid)

        # onentry через node
        if sdef.node:
            fn = self.nodes.get(sdef.node)
            if not fn:
                raise ValueError(f"Нет узла '{sdef.node}' для состояния {sid}")
            res = fn(self.state, self.config) or {}
            patch = res.get("update") or {}
            if patch:
                self.state.update(patch)
            for ev in res.get("events", []) or []:
                self.send(ev)

    def _is_done_parallel(self, parent_id: str) -> bool:
        parent = self.model.states[parent_id]
        if not parent.is_parallel:
            return False
        # считаем завершённым, если все ветки активны в final (или ушли в final-поддеревья)
        # упрощённо: каждая ветка должна иметь хотя бы один активный leaf, который is_final
        finals = set(s.id for s in self.model.states.values() if s.is_final)
        # группируем активные по прямым детям parent
        # в этом минимальном движке предполагаем, что ветка = прямой leaf/final
        for child in parent.children:
            # найдём активные leaf, которые лежат в поддереве child
            if not any(a == child or self._is_desc(a, child) for a in self.active):
                return False
        # если все ветки имеют активные leaf, считаем join возможным
        return True

    def _is_desc(self, leaf: str, ancestor: str) -> bool:
        cur = leaf
        while True:
            p = self.model.states[cur].parent
            if not p:
                return False
            if p == ancestor:
                return True
            cur = p

    def _step_transitions(self, event: Optional[str]) -> bool:
        # 1) глобальные transitions (__root__)
        fired = self._try_transitions_from("__root__", event)
        if fired:
            return True

        # 2) transitions из активных leaf (в порядке стабильном)
        for sid in list(sorted(self.active)):
            # поднимаемся вверх по иерархии: leaf -> parent -> ... -> root
            cur = sid
            while cur and cur != "__root__":
                if self._try_transitions_from(cur, event):
                    return True
                cur = self.model.states[cur].parent
        return False

    def _try_transitions_from(self, sid: str, event: Optional[str]) -> bool:
        sdef = self.model.states[sid]
        for t in sdef.transitions:
            if t.event is not None and event is not None and t.event != event:
                continue
            if t.event is not None and event is None:
                continue
            if t.event is None and event is not None:
                # без event, но пришёл event — transition без event можно считать "автоматическим" только при event=None
                continue
            if t.cond and not self._eval_cond(t.cond):
                continue

            # firing
            if t.script:
                self._run_script(t.script)

            self._goto(t.target)
            return True
        return False

    def _goto(self, target: str) -> None:
        # наивно: очищаем активные и входим в target
        # сохраняем history для всех родителей активных leaf
        for leaf in self.active:
            cur = leaf
            while cur and cur != "__root__":
                p = self.model.states[cur].parent
                if p:
                    self.history[p] = leaf
                cur = p
        self.active.clear()
        self._enter_leaf(target)

    def run(self, initial_state: Optional[Dict[str, Any]]=None, start_event: Optional[str]="start", max_steps: int=10_000) -> Dict[str, Any]:
        self.state = dict(initial_state or {})
        self.active.clear()
        self.event_queue.clear()

        self._enter_leaf(self.model.initial)
        if start_event:
            self.send(start_event)

        steps = 0
        while steps < max_steps:
            steps += 1
            if self.verbose:
                print(f"[шаг {steps}] active={self.active} queue={self.event_queue} state={self.state}")

            if not self.event_queue:
                # пробуем автоматические переходы (event=None)
                if self._step_transitions(None):
                    continue
                break

            ev = self.event_queue.pop(0)
            # переходы по событию
            if self._step_transitions(ev):
                continue

            # если событие не обработано — игнорируем
            continue

        return self.state
