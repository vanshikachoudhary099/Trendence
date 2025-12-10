# app/engine/executor.py
import asyncio
import uuid
from typing import Dict, Any, Optional
from copy import deepcopy

from ..tools.registry import get_tool
from ..engine.graph import GraphSpec, NodeSpec
from ..engine.state import RunState
from ..storage.memory import GRAPHS, RUNS

class GraphExecutor:
    def __init__(self):
        pass

    def create_graph(self, spec: GraphSpec) -> str:
        graph_id = str(uuid.uuid4())
        GRAPHS[graph_id] = {
            "nodes": {name: {
                "name": node.name,
                "func": node.func,
                "params": node.params,
                "condition": node.condition
            } for name, node in spec.nodes.items()},
            "edges": deepcopy(spec.edges),
            "start_node": spec.start_node
        }
        return graph_id

    def get_graph(self, graph_id: str) -> Dict[str, Any]:
        return GRAPHS[graph_id]

    async def run_graph(self, graph_id: str, initial_state: Dict[str, Any], run_id: Optional[str] = None):
        if run_id is None:
            run_id = str(uuid.uuid4())

        graph = GRAPHS.get(graph_id)
        if not graph:
            raise KeyError("Graph not found")

        nodes = graph["nodes"]
        edges = graph.get("edges", {})
        start = graph["start_node"]

        run = RunState(run_id=run_id, graph_id=graph_id, state=deepcopy(initial_state), status="running", current_node=start)
        RUNS[run_id] = run 

        max_iters = int(initial_state.get("max_iters", 50))
        iter_count = 0
        node_name = start

        try:
            while node_name:
                iter_count += 1
                if iter_count > max_iters:
                    run.log.append(f"Max iterations {max_iters} reached -> stopping.")
                    break

                node_meta = nodes.get(node_name)
                if not node_meta:
                    run.log.append(f"Node '{node_name}' not found; stopping.")
                    break

                run.current_node = node_name
                run.log.append(f"-> running node: {node_name}")

                func_name = node_meta["func"]
                tool = get_tool(func_name)

                try:
                    before = deepcopy(run.state)
                    
                    result = tool(run.state)
                    if isinstance(result, dict):
                        run.state = result 
                    else:
                        
                        pass
                    run.log.append(node_meta.get("params", {}).get("_log", run.state.get("log_msg", f"{func_name} executed")))
                except Exception as e:
                    run.log.append(f"Error executing tool '{func_name}': {repr(e)}")
                    run.status = "failed"
                    break

                
                next_node = edges.get(node_name)
                condition = node_meta.get("condition")
                if condition:
                    
                    picked = self._evaluate_condition_and_route(condition, next_node, run.state)
                    node_name = picked
                else:
                    
                    if isinstance(next_node, dict):
                        node_name = next_node.get("next")
                    else:
                        node_name = next_node
                await asyncio.sleep(0)
            run.status = run.status if run.status != "failed" else "failed"
            if run.status != "failed":
                run.status = "completed"
            run.final_state = deepcopy(run.state)
        except Exception as e:
            run.log.append(f"Executor error: {repr(e)}")
            run.status = "failed"
        finally:
            RUNS[run_id] = run
        return run_id

    def _evaluate_condition_and_route(self, condition: str, next_node_def, state: Dict[str, Any]):
        """
        Simple parser for conditions of the form key>=value / key==value / etc.
        If next_node_def is a dict with 'true'/'false', pick accordingly.
        If next_node_def is a string, and condition true => return it, else return None.
        """
        for op in [">=", "<=", "==", "!=", ">", "<"]:
            if op in condition:
                left, right = condition.split(op, 1)
                key = left.strip()
                raw_val = right.strip()
                try:
                    val = float(raw_val)
                except:
                    val = raw_val.strip('"').strip("'")
                cur = state.get(key)
                try:
                    cur_val = float(cur) if cur is not None else None
                except:
                    cur_val = cur

                cond_holds = False
                try:
                    if op == ">=":
                        cond_holds = float(cur_val) >= float(val)
                    elif op == "<=":
                        cond_holds = float(cur_val) <= float(val)
                    elif op == "==":
                        cond_holds = cur_val == val
                    elif op == "!=":
                        cond_holds = cur_val != val
                    elif op == ">":
                        cond_holds = float(cur_val) > float(val)
                    elif op == "<":
                        cond_holds = float(cur_val) < float(val)
                except Exception:
                    cond_holds = False

                if isinstance(next_node_def, dict):
                    return next_node_def.get("true") if cond_holds else next_node_def.get("false")
                else:
                    return next_node_def if cond_holds else None
        return None

    def get_run_snapshot(self, run_id: str):
        run = RUNS.get(run_id)
        if not run:
            return None
        return run.snapshot()
