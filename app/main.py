import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent.container_watcher import DockerWatcher
from agent.dockdns_config import DockDNSConfig
from app.api.v1.endpoints import router as v1_router

logger = logging.getLogger('dockdns.main')


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - DockDNS - %(levelname)s - %(message)s')

    dns_config = DockDNSConfig()

    logger.info(f"[FASTAPI] Starting background Docker watcher with configs {dns_config}...")
    docker_watcher = DockerWatcher(dns_config)
    docker_watcher.start()

    yield

    docker_watcher.stop()


app = FastAPI(lifespan=lifespan, title="DockDNS", version="0.1.0", )

app.include_router(v1_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI + Docker Watcher"}
