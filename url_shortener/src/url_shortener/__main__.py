import asyncio

from .domain import Base62Encoder
from .infrastructure import get_logger
from .infrastructure.config import Config
from .infrastructure.factory import create_shortener
from .presentation import serve

logger = get_logger(__name__)

if __name__ == "__main__":
    # Load configuration from environment
    config = Config.from_env()

    try:
        # Validate configuration
        config.validate()

        # Create encoder and shortener service
        encoder = Base62Encoder()
        shortener = create_shortener(config, encoder)

        logger.info(f"Starting server on {config.server.host}:{config.server.port}")
        logger.info(f"Using {config.storage.type} storage")

        # Start the server
        asyncio.run(serve(shortener, config.server.host, config.server.port))
    except Exception as err:
        logger.error(f"Failed to start server: {err}")
        raise
