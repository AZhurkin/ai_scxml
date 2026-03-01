import sys
from pathlib import Path

# Добавить корень проекта в sys.path при запуске из любой директории
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from shared.run_langgraph import run

_here = Path(__file__).resolve().parent
run(str(_here / "graph.py"), initial_state={}, config={"sources": ["s1", "s2", "s3"]}, verbose=True)
