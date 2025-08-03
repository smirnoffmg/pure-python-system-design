import pytest

from url_shortener.encoder import Base62Encoder
from url_shortener.service import Shortener
from url_shortener.storage import InMemoryStorage


@pytest.fixture()
def encoder() -> Base62Encoder:
    return Base62Encoder()


@pytest.fixture()
def storage(encoder) -> InMemoryStorage:
    return InMemoryStorage(encoder)


@pytest.fixture()
def svc(storage) -> Shortener:
    return Shortener(storage)
