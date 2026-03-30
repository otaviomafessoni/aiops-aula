import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from my_agent_app.api.router import router as api_router
from my_agent_app.collector.event_collector import EventCollector
from my_agent_app.collector.event_handler import EventHandler
from my_agent_app.database import get_database_url
from my_agent_app.web.router import router as web_router

DEFAULT_INTERVAL_MINUTES = 3


def _get_collection_interval() -> int:
    raw = os.environ.get("EVENT_COLLECTION_INTERVAL_MINUTES")
    if raw is None:
        return DEFAULT_INTERVAL_MINUTES
    try:
        value = int(raw)
        if value <= 0:
            raise ValueError("must be positive")
        return value
    except (ValueError, TypeError):
        logger.warning(
            "EVENT_COLLECTION_INTERVAL_MINUTES='%s' inválido, usando padrão %d",
            raw,
            DEFAULT_INTERVAL_MINUTES,
        )
        return DEFAULT_INTERVAL_MINUTES


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(get_database_url())
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    app.state.sessionmaker = sessionmaker

    interval = _get_collection_interval()
    handler = EventHandler(sessionmaker=sessionmaker)
    collector = EventCollector(handler=handler, interval_minutes=interval)
    collector_task = asyncio.create_task(collector.run())

    yield

    collector_task.cancel()
    try:
        await collector_task
    except asyncio.CancelledError:
        pass

    await engine.dispose()


app = FastAPI(title="My Agent App", lifespan=lifespan)
app.include_router(api_router)
app.include_router(web_router)
