import asyncio
import signal

from .handlers import HandlerRegistry
from .http_parser import HTTPRequestParser
from .http_serializer import HTTPResponseSerializer
from .logger import logger
from .service import Shortener
from .types import HTTPRequest, HTTPResponse


class RequestHandler:
    """
    Handles the application logic for incoming HTTP requests.
    """

    def __init__(self, shortener: Shortener):
        self.shortener = shortener
        self.handler_registry = HandlerRegistry(shortener)

    async def handle(self, request: HTTPRequest) -> HTTPResponse:
        handler = self.handler_registry.get_handler(request.method, request.path)
        if handler:
            return await handler.handle(request)
        else:
            from .handlers import ResponseBuilder

            return ResponseBuilder.not_found()


class HTTPProtocol(asyncio.Protocol):
    transport: asyncio.BaseTransport

    def __init__(self, request_handler: RequestHandler) -> None:
        self.request_handler = request_handler
        self._buffer = bytearray()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        self._buffer.extend(data)
        request = HTTPRequestParser.parse(self._buffer)

        if request:
            asyncio.create_task(self._process_request(request))
            self._buffer.clear()

    async def _process_request(self, request: HTTPRequest) -> None:
        response = await self.request_handler.handle(request)
        self.transport.write(HTTPResponseSerializer.serialize(response))  # type: ignore
        self.transport.close()


async def shutdown(server: asyncio.AbstractServer, sig: signal.Signals) -> None:
    logger.info(f"Received exit signal {sig.name}...")
    server.close()
    await server.wait_closed()
    logger.info("Server has shut down gracefully")
    loop = asyncio.get_running_loop()
    loop.stop()


async def serve(shortener: Shortener, host: str, port: int) -> None:
    loop = asyncio.get_running_loop()
    handler = RequestHandler(shortener)

    server = await loop.create_server(
        lambda: HTTPProtocol(handler),
        host=host,
        port=port,
    )

    logger.info(f"Serving on {host}:{port}")

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda sig=sig: asyncio.create_task(shutdown(server, sig)),  # type:ignore
        )

    # Keep server running until stopped
    await server.serve_forever()
