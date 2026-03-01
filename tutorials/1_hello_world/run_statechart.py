import sys
from pathlib import Path

# Добавить корень проекта в sys.path при запуске из любой директории
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from shared.run_statechart import run
from shared import nodes

node_map = {"initialize": nodes.initialize, "search": nodes.search, "finalize": nodes.finalize}
_here = Path(__file__).resolve().parent
run(str(_here / "diagram.scxml"), node_map, initial_state={}, config={"sources": ["s1", "s2", "s3"]}, verbose=True)
