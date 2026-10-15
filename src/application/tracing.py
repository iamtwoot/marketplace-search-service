import uuid
from contextvars import ContextVar, Token

TRACE_ID_HEADER = "X-Trace-Id"

trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


def new_trace_id() -> str:
    return uuid.uuid4().hex


def get_trace_id() -> str | None:
    return trace_id_var.get()


def set_trace_id(trace_id: str | None) -> Token[str | None]:
    return trace_id_var.set(trace_id)


def reset_trace_id(token: Token[str | None]) -> None:
    trace_id_var.reset(token)
