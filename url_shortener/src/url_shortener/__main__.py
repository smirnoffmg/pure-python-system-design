import asyncio

from .api import serve
from .encoder import Base62Encoder
from .logger import logger
from .service import Shortener
from .storage import InMemoryStorage

if __name__ == "__main__":
    encoder = Base62Encoder()
    storage = InMemoryStorage(encoder)
    shortener = Shortener(storage)

    try:
        asyncio.run(serve(shortener, "localhost", 8000))
    except Exception as err:
        logger.error(err)
