"""
Simple request logging middleware.
Logs method, path, status code, and duration for each request.
"""
import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Log each request with method, path, status, and duration."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000
        logger.info(
            "%s %s %s %.0fms",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
        return response
