import logging

from src.application.tracing import reset_trace_id, set_trace_id
from src.infrastructure.logging_config import TraceIdFilter


def make_record() -> logging.LogRecord:
    return logging.LogRecord("test", logging.INFO, __file__, 1, "msg", None, None)


def test_filter_adds_trace_id_from_context() -> None:
    record = make_record()
    token = set_trace_id("abc123")
    try:
        assert TraceIdFilter().filter(record)
    finally:
        reset_trace_id(token)

    assert record.trace_id == "abc123"


def test_filter_uses_dash_without_trace_id() -> None:
    record = make_record()

    assert TraceIdFilter().filter(record)
    assert record.trace_id == "-"
