# app/engine/graph.py
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class NodeSpec:
    name: str
    func: str                      
    params: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None  

@dataclass
class GraphSpec:
    nodes: Dict[str, NodeSpec]    
    edges: Dict[str, Any]         
    start_node: str
