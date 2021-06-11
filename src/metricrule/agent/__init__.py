'''
This package contains middleware and applications to:
- Inject middleware that creates metrics for WSGI apps
- Build an WSGI app that exports metrics.
'''
from google.protobuf import text_format
from opentelemetry.exporter.prometheus import PrometheusMetricsExporter
from opentelemetry.metrics import get_meter, set_meter_provider 
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export.controller import PushController
from prometheus_client import make_wsgi_app, make_asgi_app
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from werkzeug.wsgi import get_input_stream

from ..config_gen import metric_configuration_pb2
from .mrotel import initialize_instrument
from .mrmetric import get_instrument_specs, MetricContext
from .mrrecorder import log_request_metrics, log_response_metrics


class WSGIApplication:
    @staticmethod
    def make():
        return make_wsgi_app()


class ASGIApplication:
    @staticmethod
    def make():
        return make_asgi_app()


class WSGIMetricsMiddleware:
    '''WSGI application middleware for ML model metrics.

    Args:
        app: The WSGI application callable to forward requests to.
        config_path: The path to read the agent configuration from.
    '''

    def __init__(self, app, config_path=None) -> None:
        self.app = app
        self._config = _load_config(config_path)

        processor_mode = 'stateful'
        set_meter_provider(MeterProvider())
        self._meter = get_meter(__name__, processor_mode == 'stateful')
        exporter = PrometheusMetricsExporter('metricrule_python_agent')
        self._controller = PushController(self._meter, exporter, 5)

        specs = get_instrument_specs(self._config)
        self._input_instruments = {
            spec: initialize_instrument(self._meter, spec)
            for spec in specs[MetricContext.INPUT]
        }
        self._output_instruments = {
            spec: initialize_instrument(self._meter, spec)
            for spec in specs[MetricContext.OUTPUT]
        }

    def __call__(self, environ, start_response):
        '''The WSGI application

        Args:
            environ: A WSGI environment.
            start_response: The WSGI start_response callable.
        '''
        request_stream = get_input_stream(environ, safe_fallback=True)
        request_body = request_stream.read()
        self._get_request_metrics(request_body)
        response_stream = self.app(environ, start_response)
        response_body = b''.join(response_stream)
        self._get_response_metrics(response_body)
        return [response_body]

    def _get_request_metrics(self, request_body) -> None:
        log_request_metrics(
            self._config, self._input_instruments, self._meter, request_body)

    def _get_response_metrics(self, response_body) -> None:
        log_response_metrics(
            self._config, self._output_instruments, self._meter, response_body)


class ASGIMetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, config_path=None):
        super().__init__(app)
        self._config = _load_config(config_path)

        processor_mode = 'stateful'
        set_meter_provider(MeterProvider())
        self._meter = get_meter(__name__, processor_mode == 'stateful')
        exporter = PrometheusMetricsExporter('metricrule_python_agent')
        self._controller = PushController(self._meter, exporter, 5)

        specs = get_instrument_specs(self._config)
        self._input_instruments = {
            spec: initialize_instrument(self._meter, spec)
            for spec in specs[MetricContext.INPUT]
        }
        self._output_instruments = {
            spec: initialize_instrument(self._meter, spec)
            for spec in specs[MetricContext.OUTPUT]
        }

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_body = await request.body()
        log_request_metrics(
            self._config, self._input_instruments, self._meter, request_body)
        response = await call_next(request)
        log_response_metrics(
            self._config, self._output_instruments, self._meter, response.body)
        return response


def _load_config(config_path) -> metric_configuration_pb2.SidecarConfig:
    config_data = ''
    if len(config_path) > 0:
        with open(config_path, 'r') as config_file:
            config_data = config_file.read()
    config_proto = metric_configuration_pb2.SidecarConfig()
    text_format.Parse(config_data, config_proto)
    return config_proto
