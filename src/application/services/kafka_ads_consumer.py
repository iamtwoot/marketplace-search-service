import logging
import typing

from aiokafka import AIOKafkaConsumer, ConsumerRecord

from src.application.ports.usecases import IndexAdPort, RemoveAdPort
from src.application.tracing import (
    TRACE_ID_HEADER,
    new_trace_id,
    reset_trace_id,
    set_trace_id,
)

logger = logging.getLogger(__name__)


def trace_id_from_headers(
    headers: typing.Sequence[tuple[str, bytes | None]],
) -> str | None:
    for key, value in headers:
        if key == TRACE_ID_HEADER and value:
            return value.decode("utf-8", errors="replace")
    return None


class KafkaAdsConsumer:
    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        index_ad: IndexAdPort,
        remove_ad: RemoveAdPort,
    ) -> None:
        self._consumer = consumer
        self._index_ad = index_ad
        self._remove_ad = remove_ad

    async def run(self) -> None:
        async for msg in self._consumer:
            await self._process(msg)

    async def _process(self, msg: ConsumerRecord) -> None:
        trace_id = trace_id_from_headers(msg.headers or ()) or new_trace_id()
        token = set_trace_id(trace_id)
        try:
            try:
                await self._handle(msg.value)
            except Exception:
                logger.exception("failed to handle message %s", msg)
                return
            await self._consumer.commit()
        finally:
            reset_trace_id(token)

    async def _handle(self, value: dict[str, typing.Any]) -> None:
        event = value.get("event")
        payload = value.get("payload") or {}
        ad_id = payload.get("ad_id")
        if not isinstance(ad_id, int):
            logger.warning("skip message without ad_id: %s", value)
            return

        if event in ("ad.created", "ad.updated"):
            await self._index_ad.execute(ad_id)
        elif event == "ad.deleted":
            await self._remove_ad.execute(ad_id)
        else:
            logger.warning("unknown event type: %s", event)
            return
        logger.info("handled %s ad_id=%s", event, ad_id)
