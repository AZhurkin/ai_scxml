import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from shared.run_langgraph import run
run("langgraph.py", initial_state={}, config={"success_rate": 0.45, "max_attempts": 3}, verbose=True)
