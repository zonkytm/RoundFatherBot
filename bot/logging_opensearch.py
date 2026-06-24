import logging
import threading
import time
from datetime import UTC, datetime

from opensearchpy import OpenSearch


class OpenSearchHandler(logging.Handler):
    def __init__(
        self,
        opensearch_url: str,
        index_prefix: str = "bot-logs",
        batch_size: int = 50,
        flush_interval: float = 5.0,
    ):
        super().__init__()
        self._index_prefix = index_prefix
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._buffer: list[dict] = []
        self._lock = threading.Lock()

        host, port = opensearch_url.replace("http://", "").replace("https://", "").split(":")
        self._client = OpenSearch(
            hosts=[{"host": host, "port": int(port)}],
            http_compress=True,
            use_ssl=False,
            verify_certs=False,
        )

        self._stop_event = threading.Event()
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            doc = {
                "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "line": record.lineno,
                "function": record.funcName,
            }
            if record.exc_info and record.exc_info[1]:
                doc["exception"] = self.formatException(record.exc_info)

            with self._lock:
                self._buffer.append(doc)
                if len(self._buffer) >= self._batch_size:
                    self._flush()
        except Exception:
            self.handleError(record)

    def _flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            batch = self._buffer[:]
            self._buffer.clear()

        now = datetime.now(UTC)
        index = f"{self._index_prefix}-{now.strftime('%Y.%m')}"
        try:
            actions = []
            for doc in batch:
                actions.append({"index": {"_index": index}})
                actions.append(doc)
            if actions:
                self._client.bulk(body=actions)
        except Exception:
            pass

    def _flush_loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self._flush_interval)
            self._flush()

    def close(self) -> None:
        self._stop_event.set()
        self._flush()
        super().close()
