# app/engine/state.py
from typing import Dict, Any
from copy import deepcopy
from dataclasses import dataclass, field

@dataclass
class RunState:
    run_id: str
    graph_id: str
    state: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"   # pending/running/completed/failed
    current_node: str = ""
    log: list = field(default_factory=list)
    final_state: Dict[str, Any] = field(default_factory=dict)

    def snapshot(self):
        """Return a safe shallow copy for external inspection."""
        return {
            "run_id": self.run_id,
            "graph_id": self.graph_id,
            "state": deepcopy(self.state),
            "status": self.status,
            "current_node": self.current_node,
            "log": list(self.log),
            "final_state": deepcopy(self.final_state),
        }
