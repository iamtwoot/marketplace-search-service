import re

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.application.tracing import TRACE_ID_HEADER, new_trace_id, set_trace_id

_TRACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def resolve_trace_id(incoming: str | None) -> str:
    if incoming is not None and _TRACE_ID_PATTERN.fullmatch(incoming):
        return incoming
    return new_trace_id()


class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        trace_id = resolve_trace_id(request.headers.get(TRACE_ID_HEADER))
        set_trace_id(trace_id)
        response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response
