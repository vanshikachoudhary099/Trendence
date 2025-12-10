# Trendence – Workflow Engine (Backend Assignment)

This project implements a minimal workflow and graph execution engine using Python and FastAPI.  
It was developed as part of an AI Engineering Internship assignment to demonstrate backend design, workflow orchestration, and clean code structure.

------------------------------------------------------------

## Features

### Workflow Engine
- Supports nodes (steps) connected through edges  
- Shared state is passed between nodes  
- Conditional branching based on state  
- Looping until a condition is satisfied  
- Execution logs maintained for each run  

### Tool Registry
- Tools are simple Python functions  
- Nodes can call tools during execution  

### FastAPI Endpoints
- POST /graph/create : Create a workflow  
- POST /graph/run : Execute workflow  
- GET /graph/state/{run_id} : Get current workflow state  

------------------------------------------------------------

## Example Workflow Included: Code Review Mini-Agent

Workflow steps:
1. Extract functions from code  
2. Analyze function complexity  
3. Detect issues  
4. Suggest improvements  
5. Loop until `quality_score >= threshold`  

Implementation located in:
app/workflows/code_review.py

------------------------------------------------------------

## Project Structure

Trendence/
│
├── app/
│   ├── main.py                     (FastAPI application entry point)
│   ├── engine/
│   │   ├── graph.py                (Workflow graph and node linking)
│   │   ├── executor.py             (Workflow executor logic)
│   │   └── state.py                (Shared state model)
│   │
│   ├── storage/
│   │   └── memory.py               (In-memory storage for workflow metadata)
│   │
│   ├── tools/
│   │   └── registry.py             (Tool registration)
│   │
│   └── workflows/
│       └── code_review.py          (Example workflow implementation)
│
├── requirements.txt                 (Project dependencies)
└── README.md                        (Documentation)

------------------------------------------------------------

## Installation

1. Create a virtual environment  
   python -m venv venv

2. Activate (Windows)  
   venv\Scripts\activate

3. Install dependencies  
   pip install -r requirements.txt

------------------------------------------------------------

## Run the Application

Use the following command to start the FastAPI server:

uvicorn app.main:app --reload

API documentation available at:
http://127.0.0.1:8000/docs

------------------------------------------------------------

## Future Improvements

- Persistent database storage  
- WebSocket streaming of execution logs  
- Async background task execution  
- Workflow visualization interface  
- More example workflows  
- Unit tests

