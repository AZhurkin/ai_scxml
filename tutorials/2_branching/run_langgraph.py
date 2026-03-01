import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared.run_langgraph import run

CONFIG = {"category": "tech"}
# CONFIG = {"category": "billing"}

run("langgraph.py", initial_state={}, config=CONFIG, verbose=True)
