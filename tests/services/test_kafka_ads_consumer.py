import re
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

from src.application.ports.usecases import IndexAdPort, RemoveAdPort
from src.application.services.kafka_ads_consumer import (
    KafkaAdsConsumer,
    trace_id_from_headers,
)
from src.application.tracing import TRACE_ID_HEADER, get_trace_id


@dataclass
class FakeRecord:
    value: dict[str, Any]
    headers: tuple[tuple[str, bytes], ...] = ()


@dataclass
class FakeConsumer:
    records: list[FakeRecord]
    commits: int = 0
    trace_ids_at_commit: list[str | None] = field(default_factory=list)

    async def __aiter__(self) -> AsyncIterator[FakeRecord]:
        for record in self.records:
            yield record

    async def commit(self) -> None:
        self.commits += 1
        self.trace_ids_at_commit.append(get_trace_id())


class RecordingIndexAd(IndexAdPort):
    def __init__(self) -> None:
        self.calls: list[tuple[int, str | None]] = []

    async def execute(self, ad_id: int) -> None:
        self.calls.append((ad_id, get_trace_id()))


class RecordingRemoveAd(RemoveAdPort):
    def __init__(self) -> None:
        self.calls: list[tuple[int, str | None]] = []

    async def execute(self, ad_id: int) -> None:
        self.calls.append((ad_id, get_trace_id()))


class FailingIndexAd(IndexAdPort):
    async def execute(self, ad_id: int) -> None:
        raise RuntimeError("ad-service unavailable")


def event(name: str, ad_id: int, trace_id: str | None = None) -> FakeRecord:
    headers = () if trace_id is None else ((TRACE_ID_HEADER, trace_id.encode()),)
    return FakeRecord(
        value={"event": name, "payload": {"ad_id": ad_id}},
        headers=headers,
    )


async def test_handler_sees_trace_id_from_headers() -> None:
    consumer = FakeConsumer(
        [event("ad.created", 1, "trace-1"), event("ad.deleted", 2, "trace-2")]
    )
    index_ad, remove_ad = RecordingIndexAd(), RecordingRemoveAd()

    await KafkaAdsConsumer(consumer, index_ad, remove_ad).run()

    assert index_ad.calls == [(1, "trace-1")]
    assert remove_ad.calls == [(2, "trace-2")]
    assert consumer.trace_ids_at_commit == ["trace-1", "trace-2"]
    assert get_trace_id() is None


async def test_generates_trace_id_when_header_missing() -> None:
    consumer = FakeConsumer([event("ad.updated", 1)])
    index_ad = RecordingIndexAd()

    await KafkaAdsConsumer(consumer, index_ad, RecordingRemoveAd()).run()

    [(_, trace_id)] = index_ad.calls
    assert trace_id is not None
    assert re.fullmatch(r"[0-9a-f]{32}", trace_id)
    assert get_trace_id() is None


async def test_failed_message_is_not_committed_and_trace_is_reset() -> None:
    consumer = FakeConsumer([event("ad.created", 1, "trace-1")])

    await KafkaAdsConsumer(consumer, FailingIndexAd(), RecordingRemoveAd()).run()

    assert consumer.commits == 0
    assert get_trace_id() is None


def test_trace_id_from_headers() -> None:
    assert trace_id_from_headers([(TRACE_ID_HEADER, b"abc")]) == "abc"
    assert trace_id_from_headers([("other", b"x")]) is None
    assert trace_id_from_headers([(TRACE_ID_HEADER, None)]) is None
    assert trace_id_from_headers([]) is None
