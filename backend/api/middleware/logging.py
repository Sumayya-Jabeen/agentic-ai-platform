import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Runs automatically on every request and response.

    Before the route runs:
      - Logs the HTTP method, path, and client IP address

    After the route runs:
      - Logs the status code and how many milliseconds it took

    Example terminal output:
      2025-05-16 10:00:01  INFO  --> POST /chat  (client: 127.0.0.1)
      2025-05-16 10:00:03  INFO  <-- POST /chat  200  1842ms
      2025-05-16 10:00:03  INFO  --> GET /health  (client: 127.0.0.1)
      2025-05-16 10:00:03  INFO  <-- GET /health  200  1ms
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log the incoming request
        logger.info(
            f"--> {request.method} {request.url.path}  "
            f"(client: {request.client.host if request.client else 'unknown'})"
        )

        # Pass the request to the actual route
        response = await call_next(request)

        # Calculate how long the route took
        duration_ms = round((time.time() - start_time) * 1000)

        # Log the outgoing response
        logger.info(
            f"<-- {request.method} {request.url.path}  "
            f"{response.status_code}  {duration_ms}ms"
        )

        return response
