import logging

from src.application.tracing import get_trace_id

LOG_FORMAT = "%(asctime)s %(levelname)s [trace_id=%(trace_id)s] %(name)s: %(message)s"


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id() or "-"
        return True


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(TraceIdFilter())
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
