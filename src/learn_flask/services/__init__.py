"""build_services() is the one place concrete objects get wired together."""

from dataclasses import dataclass

from learn_flask.services.health_service import HealthService
from learn_flask.services.item_service import ItemService
from learn_flask.services.store_service import StoreService
from learn_flask.services.tag_service import TagService
from learn_flask.services.user_service import UserService

__all__ = [
    "HealthService",
    "ItemService",
    "Services",
    "StoreService",
    "TagService",
    "UserService",
    "build_services",
]


@dataclass(frozen=True)
class Services:
    users: UserService
    health: HealthService
    stores: StoreService
    items: ItemService
    tags: TagService


def build_services(session, email_sender):
    stores = StoreService(session)
    items = ItemService(session, stores)
    return Services(
        users=UserService(session, email_sender),
        health=HealthService(session),
        stores=stores,
        items=items,
        tags=TagService(session, stores, items),
    )
