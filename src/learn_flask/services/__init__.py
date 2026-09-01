"""Building the services, in one place.

build_services() is the composition root: the single spot in the whole app where
concrete objects get chosen and plugged into each other. Everywhere else works
with whatever it was handed.

That is the pay-off of injecting dependencies instead of importing them. To make
the entire application send emails to a list instead of to Brevo, you change one
argument here -- and that is exactly what the test suite does.
"""

from dataclasses import dataclass

from learn_flask.services.item_service import ItemService
from learn_flask.services.store_service import StoreService
from learn_flask.services.tag_service import TagService
from learn_flask.services.user_service import UserService

__all__ = [
    "ItemService",
    "Services",
    "StoreService",
    "TagService",
    "UserService",
    "build_services",
]


@dataclass(frozen=True)
class Services:
    """Every service, in one object, so routes fetch them with one lookup."""

    users: UserService
    stores: StoreService
    items: ItemService
    tags: TagService


def build_services(session, email_sender):
    stores = StoreService(session)
    items = ItemService(session, stores)
    return Services(
        users=UserService(session, email_sender),
        stores=stores,
        items=items,
        tags=TagService(session, stores, items),
    )
