import asyncio
import re

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.application.tracing import TRACE_ID_HEADER, get_trace_id
from src.presentation.api.middleware import TraceIdMiddleware


@pytest.fixture
def traced_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(TraceIdMiddleware)

    @app.get("/trace")
    async def trace(delay: float = 0.0) -> dict[str, str | None]:
        await asyncio.sleep(delay)
        return {"trace_id": get_trace_id()}

    return app


@pytest.fixture
async def traced_client(traced_app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=traced_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_generates_trace_id_when_header_missing(
    traced_client: AsyncClient,
) -> None:
    resp = await traced_client.get("/trace")

    trace_id = resp.headers[TRACE_ID_HEADER]
    assert re.fullmatch(r"[0-9a-f]{32}", trace_id)
    assert resp.json() == {"trace_id": trace_id}


async def test_uses_trace_id_from_header(traced_client: AsyncClient) -> None:
    resp = await traced_client.get("/trace", headers={TRACE_ID_HEADER: "abc-123"})

    assert resp.headers[TRACE_ID_HEADER] == "abc-123"
    assert resp.json() == {"trace_id": "abc-123"}


async def test_replaces_invalid_trace_id(traced_client: AsyncClient) -> None:
    resp = await traced_client.get(
        "/trace", headers={TRACE_ID_HEADER: "bad id\nwith newline"}
    )

    trace_id = resp.headers[TRACE_ID_HEADER]
    assert re.fullmatch(r"[0-9a-f]{32}", trace_id)
    assert resp.json() == {"trace_id": trace_id}


async def test_concurrent_requests_keep_own_trace_id(
    traced_client: AsyncClient,
) -> None:
    slow, fast = await asyncio.gather(
        traced_client.get(
            "/trace", params={"delay": 0.05}, headers={TRACE_ID_HEADER: "slow"}
        ),
        traced_client.get("/trace", headers={TRACE_ID_HEADER: "fast"}),
    )

    assert slow.json() == {"trace_id": "slow"}
    assert fast.json() == {"trace_id": "fast"}
