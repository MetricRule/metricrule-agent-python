
import functools
import json

from ..config_gen import metric_configuration_pb2
from . import mrmetric, mrotel

from werkzeug.wsgi import get_input_stream
from google.protobuf import text_format

from prometheus_client import start_http_server

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricsExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export.controller import PushController

class WSGIMetricsMiddleware:
    """WSGI application middleware for ML model metrics.

    Args:
        wsgi: The WSGI application callable to forward requests to.
        config_path: The path to read the agent configuration from.
    """
    def __init__(self, wsgi, config_path=None):
        self.wsgi = wsgi
        self._config = _load_config(config_path)

        start_http_server(port=8000, addr="localhost")
        processor_mode = "stateful"
        metrics.set_meter_provider(MeterProvider())
        self._meter = metrics.get_meter(__name__, processor_mode == "stateful")
        exporter = PrometheusMetricsExporter("metricrule.agent.python")
        self._controller = PushController(self._meter, exporter, 5)

        specs = mrmetric.get_instrument_specs(self._config)
        self._input_instruments =  {
            spec:mrotel.initialize_instrument(self._meter, spec) 
            for spec in specs[mrmetric.MetricContext.INPUT]
        }
        self._output_instruments = {
            spec:mrotel.initialize_instrument(self._meter, spec) 
            for spec in specs[mrmetric.MetricContext.OUTPUT]
        }

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
        self._get_request_metrics(request_body)
        start_response = self._create_start_response(start_response)
        response_stream = self.wsgi(environ, start_response)
        response_body = b"".join(response_stream)
        self._get_response_metrics(response_body)
        return response_stream

    def _get_request_metrics(self, request_body) -> None:
        # print(request_body)
        try:
            json_obj = json.loads(request_body)
        except ValueError as e:
            return
        # TODO(jishnu): Cache these labels to use with response.
        context_labels = mrmetric.get_context_labels(self._config, json_obj, mrmetric.MetricContext.INPUT)
        metrics = mrmetric.get_metric_instances(self._config, json_obj, mrmetric.MetricContext.INPUT)
        for spec, metric_instances in metrics:
            instrument = self._input_instruments[spec]
            for instance in metric_instances:
                recordings = [instrument.record(val) for val in instance.metricValues]
                labels = {label[0]:label[1] for label in instance.labels}
                labels.update({label[0]:label[1] for label in context_labels})
                self._meter.record_batch(labels, recordings)

    def _get_response_metrics(self, response_body) -> None:
        # print(response_body)
        try:
            json_obj = json.loads(response_body)
        except ValueError as e:
            return
        metrics = mrmetric.get_metric_instances(self._config, json_obj, mrmetric.MetricContext.OUTPUT)
        for spec, metric_instances in metrics:
            instrument = self._input_instruments[spec]
            for instance in metric_instances:
                recordings = [instrument.record(val) for val in instance.metricValues]
                # TODO(jishnu): Use context labels here
                labels = {label[0]:label[1] for label in instance.labels}
                self._meter.record_batch(labels, recordings)

def _load_config(config_path) -> metric_configuration_pb2.SidecarConfig:
    config_data = ''
    if len(config_path) > 0:
        with open(config_path, 'r') as f:
            config_data = f.read()
    config_proto = metric_configuration_pb2.SidecarConfig()
    text_format.Parse(config_data, config_proto)
    return config_proto