# app/tools/registry.py
from typing import Callable, Dict, Any

Tool = Callable[[Dict[str, Any]], Dict[str, Any]]

_tools: Dict[str, Tool] = {}

def register(name: str):
    """Decorator to register a tool under a name."""
    def _decorator(fn: Tool):
        _tools[name] = fn
        return fn
    return _decorator

def get_tool(name: str) -> Tool:
    if name not in _tools:
        raise KeyError(f"Tool '{name}' not found in registry.")
    return _tools[name]

def list_tools():
    return list(_tools.keys())
