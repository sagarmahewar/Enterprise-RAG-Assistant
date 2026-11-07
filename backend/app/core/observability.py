from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import Request

LOGGER_NAME = "app.observability"
_logger = logging.getLogger(LOGGER_NAME)


def get_request_id(request: Request) -> str:
    state_request_id = getattr(request.state, "request_id", None)
    if isinstance(state_request_id, str) and state_request_id:
        return state_request_id
    header_request_id = request.headers.get("X-Request-Id")
    if header_request_id:
        return header_request_id
    return "unknown-request-id"


def emit_event(event: str, **fields: Any) -> None:
    payload: dict[str, Any] = {"event": event, **fields}
    _logger.info(json.dumps(payload, separators=(",", ":"), sort_keys=True, default=str))
