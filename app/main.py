from fastapi import FastAPI
from app.api.v1.endpoints import router as v1_router
from app.agent.container_watcher import start_docker_watcher

app = FastAPI()

app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI + Docker Watcher"}

@app.on_event("startup")
def on_startup():
    print("[FASTAPI] Starting background Docker watcher...")
    start_docker_watcher()
