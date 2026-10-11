from src.application.ports.ad_source import AdSource
from src.application.ports.uow import UnitOfWork
from src.application.ports.usecases import IndexAdPort


class IndexAd(IndexAdPort):
    def __init__(self, uow: UnitOfWork, ad_source: AdSource) -> None:
        self._uow = uow
        self._ad_source = ad_source

    async def execute(self, ad_id: int) -> None:
        snapshot = await self._ad_source.get(ad_id)
        async with self._uow:
            if snapshot is None or snapshot.status != "active":
                await self._uow.search.delete(ad_id)
            else:
                await self._uow.search.upsert(
                    ad_id=snapshot.ad_id,
                    title=snapshot.title,
                    description=snapshot.description,
                    price=snapshot.price,
                    category=snapshot.category,
                    city=snapshot.city,
                )
            await self._uow.commit()
