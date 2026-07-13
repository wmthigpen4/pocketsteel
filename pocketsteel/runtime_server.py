"""Bounded single-process threaded WSGI runtime for the private application."""

from __future__ import annotations

import logging
import os
import re
import signal
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any, Callable
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer


LOGGER = logging.getLogger("pocketsteel.runtime")
RUNTIME_THREADS_ENV = "STEEL_RAG_RUNTIME_THREADS"
RUNTIME_QUEUE_ENV = "STEEL_RAG_RUNTIME_QUEUE"
RUNTIME_LOG_DIR_ENV = "STEEL_RAG_LOG_DIR"
DEFAULT_RUNTIME_THREADS = 8
DEFAULT_RUNTIME_QUEUE = 32


def bounded_env_int(name: str, default: int, *, minimum: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name) or default)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def configure_runtime_logging() -> None:
    """Configure one size-bounded runtime log without exposing request queries."""

    if LOGGER.handlers:
        return
    log_dir = str(os.environ.get(RUNTIME_LOG_DIR_ENV) or "").strip()
    if log_dir:
        path = Path(log_dir).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = RotatingFileHandler(
            path / "runtime.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


class BoundedRequestHandler(WSGIRequestHandler):
    """Log bounded request metadata while omitting query strings and identities."""

    _QUERY_RE = re.compile(r"(\s)(/[^\s?]*)(?:\?[^\s]*)?(\sHTTP/)")

    def log_message(self, format: str, *args: Any) -> None:
        message = (format % args) if args else format
        message = self._QUERY_RE.sub(r"\1\2\3", message)
        LOGGER.info("client=%s %s", self.client_address[0], message[:512])


class BoundedThreadingWSGIServer(ThreadingMixIn, WSGIServer):
    """Share one application/model instance across a bounded worker set."""

    daemon_threads = False
    block_on_close = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        request_handler_class: type[WSGIRequestHandler] = BoundedRequestHandler,
        *,
        max_workers: int = DEFAULT_RUNTIME_THREADS,
        request_queue: int = DEFAULT_RUNTIME_QUEUE,
    ) -> None:
        self.max_workers = max(2, min(int(max_workers), 32))
        self.request_queue_size = max(self.max_workers, min(int(request_queue), 128))
        self._worker_slots = threading.BoundedSemaphore(self.max_workers)
        super().__init__(server_address, request_handler_class)

    def process_request(self, request: Any, client_address: tuple[str, int]) -> None:
        if not self._worker_slots.acquire(blocking=False):
            self._reject_busy_request(request)
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._worker_slots.release()
            raise

    def process_request_thread(self, request: Any, client_address: tuple[str, int]) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._worker_slots.release()

    @staticmethod
    def _reject_busy_request(request: Any) -> None:
        body = b'{"error":"server is busy"}'
        response = (
            b"HTTP/1.1 503 Service Unavailable\r\n"
            b"Content-Type: application/json; charset=utf-8\r\n"
            + f"Content-Length: {len(body)}\r\n".encode("ascii")
            + b"Cache-Control: no-store\r\nConnection: close\r\n\r\n"
            + body
        )
        try:
            request.sendall(response)
        except OSError:
            return


def create_runtime_server(
    host: str,
    port: int,
    app: Callable[..., Any],
    *,
    max_workers: int | None = None,
    request_queue: int | None = None,
) -> BoundedThreadingWSGIServer:
    configure_runtime_logging()
    server = BoundedThreadingWSGIServer(
        (host, int(port)),
        BoundedRequestHandler,
        max_workers=max_workers
        or bounded_env_int(RUNTIME_THREADS_ENV, DEFAULT_RUNTIME_THREADS, minimum=2, maximum=32),
        request_queue=request_queue
        or bounded_env_int(RUNTIME_QUEUE_ENV, DEFAULT_RUNTIME_QUEUE, minimum=8, maximum=128),
    )
    server.set_app(app)
    return server


def serve_runtime(
    host: str,
    port: int,
    app: Callable[..., Any],
    *,
    on_ready: Callable[[BoundedThreadingWSGIServer], None] | None = None,
    max_workers: int | None = None,
    request_queue: int | None = None,
) -> None:
    """Serve until SIGINT/SIGTERM, then stop accepting work and join workers."""

    server = create_runtime_server(
        host,
        port,
        app,
        max_workers=max_workers,
        request_queue=request_queue,
    )
    stopping = threading.Event()

    def request_shutdown(signum: int, _frame: Any) -> None:
        if stopping.is_set():
            return
        stopping.set()
        LOGGER.info("shutdown_requested signal=%s", signum)
        threading.Thread(target=server.shutdown, name="wsgi-shutdown", daemon=True).start()

    previous_handlers: dict[int, Any] = {}
    if threading.current_thread() is threading.main_thread():
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous_handlers[signum] = signal.getsignal(signum)
            signal.signal(signum, request_shutdown)
    try:
        if on_ready is not None:
            on_ready(server)
        LOGGER.info(
            "runtime_ready host=%s port=%s threads=%s queue=%s",
            host,
            port,
            server.max_workers,
            server.request_queue_size,
        )
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        LOGGER.info("runtime_stopped")
