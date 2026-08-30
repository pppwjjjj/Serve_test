"""core 包：封装 requests，是 service 层与 HTTP 世界之间的唯一通道。"""

from core.client import Client
from core.exceptions import (
    APIError,
    BadRequestError,
    ForbiddenError,
    UnauthorizedError,
    raise_for_api_error,
)

__all__ = [
    "Client",
    "APIError",
    "BadRequestError",
    "ForbiddenError",
    "UnauthorizedError",
    "raise_for_api_error",
]
