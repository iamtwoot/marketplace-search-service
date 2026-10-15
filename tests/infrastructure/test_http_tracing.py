import httpx

from src.application.tracing import TRACE_ID_HEADER, reset_trace_id, set_trace_id
from src.infrastructure.http.tracing import inject_trace_id


def make_client(seen: list[httpx.Request]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    return httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        event_hooks={"request": [inject_trace_id]},
    )


async def test_outgoing_request_carries_trace_id() -> None:
    seen: list[httpx.Request] = []
    token = set_trace_id("trace-http")
    try:
        async with make_client(seen) as client:
            await client.get("http://ad/internal/ads/1")
    finally:
        reset_trace_id(token)

    assert seen[0].headers[TRACE_ID_HEADER] == "trace-http"


async def test_outgoing_request_without_trace_id_has_no_header() -> None:
    seen: list[httpx.Request] = []
    async with make_client(seen) as client:
        await client.get("http://ad/internal/ads/1")

    assert TRACE_ID_HEADER not in seen[0].headers
