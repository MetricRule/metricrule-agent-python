"""Middleware to instrument WSGI application and WSGI view for metrics.

This module provides two classes:

1) A middleware to be used with WSGI webservers that records metrics.

   Usage:
      # app is some WSGI application.
      app = WSGIMetricsMiddleware(app, config_path=/some/path/to/config/file)

2) An application that provides a view of the recorded metrics.

   Usage:
     app = Flask('MetricsView')
     app.wsgi_app = WSGIApplication.make()
     app.run('127.0.0.1', '9001', debug=True)
"""
from collections import deque
from typing import Deque

from prometheus_client import make_wsgi_app
from werkzeug.wsgi import get_input_stream

from .mrconfig import load_config
from .mrotel import initialize_all_instruments
from .mrmetric import MetricContext
from .mrrecorder import log_request_metrics, log_response_metrics


class WSGIApplication:
    """A WSGI application to view collected metrics.
    """
    @staticmethod
    def make():
        """Makes a new WSGI application.
        """
        return make_wsgi_app()


class WSGIMetricsMiddleware:
    """WSGI application middleware for requests and responses.

    Attributes:
        app: The WSGI application callable to forward requests to.
    """

    def __init__(self, app, config_path=None) -> None:
        """Initializes middleware for the given app.

        Args:
          app: The WSGI application to be called.
          config_path: The path to read agent config from.
        """
        self.app = app
        self._config = load_config(config_path)
        self._instruments = initialize_all_instruments(self._config)
        self._context_labels: Deque[tuple[tuple[str, str], ...]] = deque()

    def __call__(self, environ, start_response):
        """The WSGI application

        Args:
            environ: A WSGI environment.
            start_response: The WSGI start_response callable.
        """
        request_stream = get_input_stream(environ, safe_fallback=True)
        request_body = request_stream.read()
        self._get_request_metrics(request_body)
        response_stream = self.app(environ, start_response)
        response_body = b''.join(response_stream)
        self._get_response_metrics(response_body)
        return [response_body]

    def _get_request_metrics(self, request_body) -> None:
        self._context_labels.clear()
        log_request_metrics(
            self._config,
            self._instruments[MetricContext.INPUT],
            request_body,
            self._context_labels)

    def _get_response_metrics(self, response_body) -> None:
        log_response_metrics(
            self._config,
            self._instruments[MetricContext.OUTPUT],
            response_body,
            self._context_labels)
