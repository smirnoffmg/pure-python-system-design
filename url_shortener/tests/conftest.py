import pytest

from url_shortener.application import Shortener
from url_shortener.domain import Base62Encoder
from url_shortener.infrastructure import InMemoryStorage


@pytest.fixture()
def encoder() -> Base62Encoder:
    return Base62Encoder()


@pytest.fixture()
def storage(encoder) -> InMemoryStorage:
    return InMemoryStorage(encoder)


@pytest.fixture()
def svc(storage) -> Shortener:
    return Shortener(storage)
