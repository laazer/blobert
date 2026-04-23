from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from fastapi import HTTPException

SAFE_INTERNAL_ERROR_DETAIL = "Internal server error"


@dataclass(frozen=True)
class ErrorMappingRule:
    exception_type: type[BaseException]
    status_code: int
    detail_builder: Callable[[BaseException], str]


def is_safe_client_detail(detail: str) -> bool:
    lowered = detail.lower()
    sensitive_markers = ("secret", "token", "password", "apikey", "api_key")
    return all(marker not in lowered for marker in sensitive_markers)


def map_exception_to_http(
    exc: BaseException,
    *,
    route: str,
    logger: logging.Logger,
    rules: tuple[ErrorMappingRule, ...],
    fallback_status_code: int = 500,
    fallback_detail: str = SAFE_INTERNAL_ERROR_DETAIL,
) -> HTTPException:
    for rule in rules:
        if isinstance(exc, rule.exception_type):
            return HTTPException(status_code=rule.status_code, detail=rule.detail_builder(exc))

    logger.error(
        "Unhandled backend exception mapped to safe fallback",
        exc_info=True,
        extra={"route": route, "exception_type": type(exc).__name__},
    )
    return HTTPException(status_code=fallback_status_code, detail=fallback_detail)
