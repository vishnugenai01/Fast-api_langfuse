from time import perf_counter
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from config.langfuse_client import (
    LANGFUSE_ENABLED,
    flush_langfuse,
    langfuse,
)

from routers.chat_messages import router as chat_messages_router
from routers.items import router as items_router
from routers.restaurants import router as restaurants_router
from routers.Orders import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    yield
    flush_langfuse()


app = FastAPI(
    title="Food Ordering API",
    lifespan=lifespan,
)


@app.middleware("http")
async def langfuse_request_tracing(
    request: Request,
    call_next,
):
    """Trace HTTP requests without recording bodies or secrets."""

    if not LANGFUSE_ENABLED or langfuse is None:
        return await call_next(request)

    started = perf_counter()
    route_path = request.url.path

    # Continue serving requests if tracing cannot be started.
    try:
        observation_context = langfuse.start_as_current_observation(
            as_type="span",
            name=f"HTTP {request.method} {route_path}",
        )
    except Exception:
        return await call_next(request)

    with observation_context as observation:
        try:
            observation.update(
                input={
                    "method": request.method,
                    "path": route_path,
                },
                metadata={
                    "component": "food-ordering-api",
                },
            )
        except Exception:
            pass

        try:
            response = await call_next(request)

        except Exception as exc:
            try:
                observation.update(
                    output={
                        "status_code": 500,
                        "outcome": "error",
                    },
                    metadata={
                        "duration_ms": round(
                            (perf_counter() - started) * 1000,
                            2,
                        ),
                        "error_type": type(exc).__name__,
                    },
                )
            except Exception:
                pass

            raise

        try:
            observation.update(
                output={
                    "status_code": response.status_code,
                    "outcome": (
                        "success"
                        if response.status_code < 400
                        else "http_error"
                    ),
                },
                metadata={
                    "duration_ms": round(
                        (perf_counter() - started) * 1000,
                        2,
                    ),
                },
            )
        except Exception:
            pass

        return response


app.include_router(chat_messages_router)
app.include_router(items_router)
app.include_router(restaurants_router)
app.include_router(orders_router)
