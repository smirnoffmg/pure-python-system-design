import asyncio

from .application import Shortener
from .domain import Base62Encoder
from .infrastructure import InMemoryStorage, get_logger
from .presentation import serve

logger = get_logger(__name__)

if __name__ == "__main__":
    encoder = Base62Encoder()
    storage = InMemoryStorage(encoder)
    shortener = Shortener(storage)

    try:
        asyncio.run(serve(shortener, "localhost", 8000))
    except Exception as err:
        logger.error(err)
