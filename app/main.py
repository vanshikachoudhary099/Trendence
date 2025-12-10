# app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import uuid

from .engine.executor import GraphExecutor
from .workflows.code_review import build_code_review_graph
from .tools.registry import list_tools
from .storage.memory import RUNS, GRAPHS

app = FastAPI(title="Workflow Engine - Mini")

executor = GraphExecutor()

@app.on_event("startup")
async def startup_event():
    # create and store a sample code-review graph
    spec = build_code_review_graph(threshold=80)
    graph_id = executor.create_graph(spec)
    app.state.sample_graph_id = graph_id

@app.get("/tools")
def _list_tools():
    return {"tools": list_tools()}

@app.post("/graph/create")
def create_graph(spec: dict):
    # spec expected to be in the serialized shape of GraphSpec (nodes mapping etc).
    # For quickness this endpoint accepts the dict form; in a later iteration we would validate.
    # Users can use the builder functions locally (like build_code_review_graph)
    # We'll accept minimal validation:
    if not spec.get("nodes") or not spec.get("start_node"):
        raise HTTPException(status_code=400, detail="Invalid graph spec: 'nodes' and 'start_node' required.")
    # Convert nodes dict entries into NodeSpec if needed — executor.create_graph expects serializable dict anyway
    # We'll store directly:
    graph_id = str(uuid.uuid4())
    GRAPHS[graph_id] = spec
    return {"graph_id": graph_id}

@app.post("/graph/run")
async def run_graph(payload: dict, background_tasks: BackgroundTasks):
    graph_id = payload.get("graph_id")
    initial_state = payload.get("initial_state", {})
    if graph_id not in GRAPHS:
        raise HTTPException(status_code=404, detail="Graph not found")
    run_id = str(uuid.uuid4())
    # schedule executor.run_graph as background task
    background_tasks.add_task(executor.run_graph, graph_id, initial_state, run_id)
    return {"run_id": run_id, "message": "Run started"}

@app.get("/graph/state/{run_id}")
def get_run_state(run_id: str):
    snapshot = executor.get_run_snapshot(run_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return snapshot

@app.get("/graph/sample")
def get_sample_graph():
    return {"sample_graph_id": app.state.sample_graph_id}

# Optional websocket for streaming logs.
@app.websocket("/ws/run/{run_id}")
async def websocket_logs(websocket: WebSocket, run_id: str):
    await websocket.accept()
    last_len = 0
    try:
        while True:
            snapshot = executor.get_run_snapshot(run_id)
            if not snapshot:
                await websocket.send_json({"error": "run_not_found"})
                break
            logs = snapshot["log"]
            # send new logs
            if len(logs) > last_len:
                for entry in logs[last_len:]:
                    await websocket.send_json({"log": entry})
                last_len = len(logs)
            if snapshot["status"] in ("completed", "failed"):
                await websocket.send_json({"status": snapshot["status"], "final_state": snapshot["final_state"]})
                break
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
