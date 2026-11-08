"""Typed provider errors so callers can decide retry / fallback / report."""
from __future__ import annotations

from typing import Optional


class ProviderError(Exception):
    code = "provider_error"
    retryable = False

    def __init__(self, message: str, provider: str = "", status: Optional[int] = None,
                 retry_after: Optional[float] = None):
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.status = status
        self.retry_after = retry_after

    def to_dict(self) -> dict:
        return {"code": self.code, "provider": self.provider, "status": self.status,
                "message": self.message}


class NotConfigured(ProviderError):
    code = "not_configured"


class AuthError(ProviderError):
    code = "auth_failed"


class RateLimited(ProviderError):
    code = "rate_limited"
    retryable = False  # fall back / report instead of hammering


class ModelUnavailable(ProviderError):
    code = "model_unavailable"


class UpstreamError(ProviderError):
    code = "upstream_error"
    retryable = True


class UpstreamTimeout(ProviderError):
    code = "timeout"
    retryable = True


class NetworkError(ProviderError):
    code = "network_error"
    retryable = True


class EmptyResponse(ProviderError):
    code = "empty_response"
    retryable = True


class BadRequest(ProviderError):
    code = "bad_request"
