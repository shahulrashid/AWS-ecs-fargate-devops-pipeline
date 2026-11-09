import logging
import os
import time
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, Response

from .database import TaskRepository, get_repository
from .models import Task, TaskCreate, TaskUpdate

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
logger = logging.getLogger("task-api")

app = FastAPI(title="Task Management API", version="1.0.0")

_repo: TaskRepository = get_repository()


def repo() -> TaskRepository:
    return _repo


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception:
        logger.exception("unhandled error %s %s", request.method, request.url.path)
        raise
    ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s (%.1f ms)", request.method, request.url.path, response.status_code, ms)
    return response


@app.get("/health")
def health():
    """Liveness check used by the ALB target group and the ECS container health check."""
    return {"status": "ok"}


@app.get("/health/ready")
def ready(r: TaskRepository = Depends(repo)):
    """Readiness check: verifies the database is reachable."""
    try:
        r.ping()
    except Exception as exc:
        logger.error("readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="database unavailable")
    return {"status": "ready"}


@app.get("/tasks", response_model=List[Task])
def list_tasks(r: TaskRepository = Depends(repo)):
    return r.list()


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str, r: TaskRepository = Depends(repo)):
    task = r.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(data: TaskCreate, r: TaskRepository = Depends(repo)):
    return r.create(data)


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: str, data: TaskUpdate, r: TaskRepository = Depends(repo)):
    task = r.update(task_id, data)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, r: TaskRepository = Depends(repo)):
    if not r.delete(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)
