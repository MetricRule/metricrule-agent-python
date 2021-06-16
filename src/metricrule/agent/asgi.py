"""Middleware to instrument ASGI application and ASGI view for metrics.

This module provides two classes:

1) A middleware to be used with ASGI webservers that records metrics.

   Usage:
      # app is some ASGI application.
      app = ASGIMetricsMiddleware(app, config_path=/some/path/to/config/file)

2) An application that provides a view of the recorded metrics.

   Usage:
     # In some file main.py
     app = ASGIApplication.make()
     uvicorn main:app
"""
from collections import deque

from prometheus_client import make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from .mrconfig import load_config
from .mrotel import initialize_all_instruments
from .mrmetric import MetricContext
from .mrrecorder import log_request_metrics, log_response_metrics


class ASGIApplication:
    """An ASGI application to view collected metrics.
    """
    @staticmethod
    def make():
        """Makes a new ASGI application.
        """
        return make_asgi_app()


class ASGIMetricsMiddleware(BaseHTTPMiddleware):
    """ASGI middleware to log metrics for requests and responses.
    """

    class LoggingResponse(Response):
        """A response subclass that logs before forwarding the response.

        If the response is streamed, it will be cached until the payload
        is complete and logging is done.
        """

        def __init__(self, original_response, log_fn):
            self.original_response = original_response
            self.log_fn = log_fn
            self.chunks = b''

        async def __call__(self, scope, receive, send) -> None:
            async def logging_send(message) -> None:
                if 'body' in message:
                    self.chunks += message['body']
                if not 'more_body' in message or not message['more_body']:
                    self.log_fn(self.chunks)
                await send(message)

            await self.original_response(scope, receive, logging_send)

    def __init__(self, app, config_path=None):
        """Initializes middleware for the given app.

        Args:
          app: The ASGI application to be called.
          config_path: The path to read agent config from.
        """
        super().__init__(app)
        self._config = load_config(config_path)
        self._instruments = initialize_all_instruments(self._config)
        self._context_labels = deque()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Middleware implementation that logs requests and responses.
        """
        request_body = await request.body()
        self._context_labels.clear()
        log_request_metrics(
            self._config,
            self._instruments[MetricContext.INPUT],
            request_body,
            self._context_labels)
        response = await call_next(request)
        if response.status_code == 200:
            logging_response = ASGIMetricsMiddleware.LoggingResponse(
                response, lambda r: log_response_metrics(
                    self._config,
                    self._instruments[MetricContext.OUTPUT],
                    r,
                    self._context_labels))
            return logging_response
        return response
