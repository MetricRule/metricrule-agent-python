
import functools

class WSGIMetricsMiddleware:
    """WSGI application middleware for ML model metrics.

    Args:
        wsgi: The WSGI application callable to forward requests to.
    """
    def __init__(self, wsgi):
        self.wsgi = wsgi

    @staticmethod
    def _create_start_response(start_response):
        @functools.wraps(start_response)
        def _start_response(status, response_headers, *args, **kwargs):
            return start_response(status, response_headers, *args, **kwargs)

        return _start_response
    
    def __call__(self, environ, start_response):
        """The WSGI application

        Args:
            environ: A WSGI environment.
            start_response: The WSGI start_response callable.
        """
        start_response = self._create_start_response(start_response)
        return self.wsgi(environ, start_response)

