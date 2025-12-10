# app/workflows/code_review.py
from typing import Dict, Any
from ..engine.graph import GraphSpec, NodeSpec
from ..tools.registry import register

# --- tools (registered under names) ---
@register("extract_functions")
def extract_functions(state: Dict[str, Any]) -> Dict[str, Any]:
    code = state.get("code", "")
    funcs = []
    cur_name = None
    cur_body = []
    for line in code.splitlines():
        if line.strip().startswith("def "):
            if cur_name:
                funcs.append({"name": cur_name, "body": "\n".join(cur_body)})
            header = line.strip()
            try:
                name = header.split("def")[1].split("(")[0].strip()
            except:
                name = "unknown"
            cur_name = name
            cur_body = [line]
        elif cur_name:
            cur_body.append(line)
    if cur_name:
        funcs.append({"name": cur_name, "body": "\n".join(cur_body)})
    state["functions"] = funcs
    state["log_msg"] = f"extracted {len(funcs)} func(s)"
    return state

@register("check_complexity")
def check_complexity(state: Dict[str, Any]) -> Dict[str, Any]:
    funcs = state.get("functions", [])
    threshold = int(state.get("complexity_threshold", 15))
    issues = state.setdefault("issues", [])
    for f in funcs:
        line_count = f["body"].count("\n") + 1
        if line_count > threshold:
            issues.append({"func": f["name"], "issue": "complex", "lines": line_count})
    state["issues"] = issues
    state["quality_score"] = max(0, 100 - len(issues) * 30)
    state["log_msg"] = f"complexity checked; issues={len(issues)}; score={state['quality_score']}"
    return state

@register("detect_issues")
def detect_issues(state: Dict[str, Any]) -> Dict[str, Any]:
    code = state.get("code", "")
    issues = state.setdefault("issues", [])
    for i, line in enumerate(code.splitlines(), start=1):
        if "TODO" in line or "FIXME" in line:
            issues.append({"line": i, "issue": "todo", "text": line.strip()})
        if len(line) > 120:
            issues.append({"line": i, "issue": "long_line", "len": len(line)})
        if "print(" in line and "debug" not in line.lower():
            issues.append({"line": i, "issue": "debug_print", "text": line.strip()})
    state["issues"] = issues
    state["log_msg"] = f"detected {len(issues)} issues"
    return state

@register("suggest_improvements")
def suggest_improvements(state: Dict[str, Any]) -> Dict[str, Any]:
    suggestions = state.setdefault("suggestions", [])
    for issue in state.get("issues", []):
        kind = issue.get("issue")
        if kind == "complex":
            suggestions.append(f"Refactor function {issue.get('func')} (lines={issue.get('lines')})")
        elif kind == "todo":
            suggestions.append(f"Resolve TODO at line {issue.get('line')}")
        elif kind == "long_line":
            suggestions.append(f"Wrap long line at {issue.get('line')}")
        elif kind == "debug_print":
            suggestions.append(f"Remove debug 'print' at {issue.get('line')}")
    # small simulated improvement
    state["quality_score"] = min(100, state.get("quality_score", 0) + len(suggestions) * 5)
    state["log_msg"] = f"suggested {len(suggestions)} improvements; new_score={state['quality_score']}"
    return state

# --- Graph builder ---
def build_code_review_graph(threshold: int = 80) -> GraphSpec:
    nodes = {
        "extract": NodeSpec(name="extract", func="extract_functions"),
        "complexity": NodeSpec(name="complexity", func="check_complexity"),
        "detect": NodeSpec(name="detect", func="detect_issues"),
        "suggest": NodeSpec(name="suggest", func="suggest_improvements", condition=f"quality_score>={threshold}")
    }

    edges = {
        "extract": "complexity",
        "complexity": "detect",
        "detect": "suggest",
        "suggest": {"true": None, "false": "extract"}
    }

    return GraphSpec(nodes=nodes, edges=edges, start_node="extract")
