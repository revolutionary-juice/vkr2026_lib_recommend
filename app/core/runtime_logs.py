from collections import deque
from datetime import datetime, timezone
from typing import Deque


FAILED_REQUESTS: Deque[dict] = deque(maxlen=200)
ERROR_EVENTS: Deque[dict] = deque(maxlen=200)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_failed_request(path: str, method: str, status_code: int, detail: str | None = None) -> None:
    FAILED_REQUESTS.appendleft(
        {
            "timestamp": _utc_now(),
            "path": path,
            "method": method,
            "status_code": status_code,
            "detail": detail or "",
        }
    )


def log_error_event(path: str, method: str, error: str) -> None:
    ERROR_EVENTS.appendleft(
        {
            "timestamp": _utc_now(),
            "path": path,
            "method": method,
            "error": error,
        }
    )


def get_failed_requests() -> list[dict]:
    return list(FAILED_REQUESTS)


def get_error_events() -> list[dict]:
    return list(ERROR_EVENTS)
