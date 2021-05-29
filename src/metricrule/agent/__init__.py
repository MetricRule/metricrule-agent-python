
import functools
from ..config_gen import metric_configuration_pb2

from werkzeug.wsgi import get_input_stream
from google.protobuf import text_format

class WSGIMetricsMiddleware:
    """WSGI application middleware for ML model metrics.

    Args:
        wsgi: The WSGI application callable to forward requests to.
        config_path: The path to read the agent configuration from.
    """
    def __init__(self, wsgi, config_path=None):
        self.wsgi = wsgi
        self.config_path = config_path

        self._load_config()

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
        request_stream = get_input_stream(environ, safe_fallback=True)
        request_body = request_stream.read()
        print(request_body)
        start_response = self._create_start_response(start_response)
        response_stream = self.wsgi(environ, start_response)
        response_body = b"".join(response_stream)
        print(response_body)
        return response_stream

    def _load_config(self):
        # Read file
        config_data = ''
        if len(self.config_path) > 0:
            with open(self.config_path, 'r') as f:
                config_data = f.read()
        # Load into proto
        config_proto = metric_configuration_pb2.SidecarConfig()
        text_format.Parse(config_data, config_proto)
        self.config = config_proto
