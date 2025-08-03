import asyncio
import json
import signal

from .logger import logger
from .service import Shortener


class HTTPRequest:
    """
    Represents an HTTP request parsed from raw bytes.
    """

    method: str
    path: str
    version: str

    def __init__(self, raw_data: bytes):
        # self.method: str | None = None
        # self.path: str | None = None
        # self.version: str | None = None
        self.headers: dict[str, str] = {}
        self.body: str | None = None
        self.content_length = 0
        self.finished = False

        self._parse(raw_data)

    def _parse(self, data: bytes) -> None:
        try:
            header_part, _, body_part = data.partition(b"\r\n\r\n")
            header_lines = header_part.decode().split("\r\n")

            if not header_lines:
                return

            request_line = header_lines[0]
            self.method, self.path, self.version = request_line.split(" ")

            for line in header_lines[1:]:
                if not line.strip():
                    continue
                key, val = line.split(":", 1)
                self.headers[key.strip().lower()] = val.strip()

            self.content_length = int(self.headers.get("content-length", 0))
            # Check if full body is received
            if len(body_part) >= self.content_length:
                self.body = body_part[: self.content_length].decode()
                self.finished = True
        except Exception as e:
            logger.error(f"Failed to parse HTTP request: {e}")
            # Parsing error means incomplete or invalid request, so finished = False

    def is_complete(self) -> bool:
        return self.finished


class HTTPResponse:
    """
    Helper class to build HTTP responses.
    """

    def __init__(
        self,
        status_code: int,
        status_message: str,
        body: dict | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.status_message = status_message
        self.body = body
        self.headers = headers or {}

    def serialize(self) -> bytes:
        lines = [f"HTTP/1.1 {self.status_code} {self.status_message}"]
        if self.body is not None:
            body_str = json.dumps(self.body)
            self.headers["Content-Length"] = str(len(body_str))
            self.headers["Content-Type"] = "application/json"
        else:
            body_str = ""

        self.headers["Connection"] = "close"

        lines.extend(f"{key}: {value}" for key, value in self.headers.items())
        lines.append("")
        lines.append(body_str)

        return "\r\n".join(lines).encode()


class RequestHandler:
    """
    Handles the application logic for incoming HTTP requests.
    """

    def __init__(self, shortener: Shortener):
        self.shortener = shortener

    async def handle(self, request: HTTPRequest) -> HTTPResponse:
        if request.method == "POST" and request.path == "/shorten":
            return await self._handle_shorten(request)
        elif request.method == "GET" and request.path.startswith("/"):
            return await self._handle_redirect(request)
        else:
            return HTTPResponse(404, "Not Found")

    async def _handle_shorten(self, request: HTTPRequest) -> HTTPResponse:
        if not request.body:
            return HTTPResponse(400, "Bad Request", {"error": "Empty request body"})

        try:
            data = json.loads(request.body)
            full_url = data.get("url")
            if not full_url:
                return HTTPResponse(
                    400, "Bad Request", {"error": "URL parameter is required"}
                )
            short_url = await self.shortener.get_short_url(full_url)
            return HTTPResponse(201, "Created", {"short_url": short_url})
        except json.JSONDecodeError:
            return HTTPResponse(400, "Bad Request", {"error": "Invalid JSON format"})
        except Exception as e:
            logger.error(f"Error in POST /shorten: {e}")
            return HTTPResponse(500, "Internal Server Error")

    async def _handle_redirect(self, request: HTTPRequest) -> HTTPResponse:
        short_code = request.path.lstrip("/")
        try:
            full_url = await self.shortener.get_full_url(short_code)
            if full_url:
                return HTTPResponse(302, "Found", headers={"Location": full_url})
            else:
                return HTTPResponse(404, "Not Found")
        except Exception as e:
            logger.error(f"Error in GET /{short_code}: {e}")
            return HTTPResponse(500, "Internal Server Error")


class HTTPProtocol(asyncio.Protocol):
    transport: asyncio.BaseTransport

    def __init__(self, request_handler: RequestHandler) -> None:
        self.request_handler = request_handler
        self._processing = False
        self._buffer = bytearray()

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.transport = transport

    def data_received(self, data: bytes) -> None:
        self._buffer.extend(data)
        if self._processing:
            return  # Prevent concurrent processing

        request = HTTPRequest(self._buffer)
        if request.is_complete():
            self._processing = True
            asyncio.create_task(self._process_request(request))

    async def _process_request(self, request: HTTPRequest) -> None:
        response = await self.request_handler.handle(request)
        self.transport.write(response.serialize())  # type: ignore
        self.transport.close()
        self._processing = False
        self._buffer.clear()


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
