import httpx

from src.application.tracing import TRACE_ID_HEADER, get_trace_id


async def inject_trace_id(request: httpx.Request) -> None:
    trace_id = get_trace_id()
    if trace_id is not None:
        request.headers[TRACE_ID_HEADER] = trace_id
