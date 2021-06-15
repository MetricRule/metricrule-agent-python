'''
'''
import json
from typing import Union

from ..config_gen.metric_configuration_pb2 import SidecarConfig
from .mrmetric import get_context_labels, get_metric_instances, MetricContext, MetricInstrumentSpec
from .mrotel import Instrument

InstrumentMap = dict[MetricInstrumentSpec, Instrument]


def log_request_metrics(config: SidecarConfig,
                        input_instruments: InstrumentMap,
                        request_body: Union[str, bytes]) -> None:
    print(request_body)
    try:
        json_obj = json.loads(request_body)
    except ValueError:
        return
    # TODO(jishnu): Cache these labels to use with response.
    context_labels = get_context_labels(
        config, json_obj, MetricContext.INPUT)
    metric_instances = get_metric_instances(
        config, json_obj, MetricContext.INPUT)
    for spec, instances in metric_instances.items():
        instrument = input_instruments[spec]
        for instance in instances:
            labels = {label[0]: label[1] for label in instance.labels}
            labels.update({label[0]: label[1] for label in context_labels})
            _ = [instrument.record(val, labels)
                 for val in instance.metricValues]


def log_response_metrics(config: SidecarConfig,
                         output_instruments: InstrumentMap,
                         response_body: Union[str, bytes]) -> None:
    print(response_body)
    try:
        json_obj = json.loads(response_body)
    except ValueError:
        return
    metric_instances = get_metric_instances(
        config, json_obj, MetricContext.OUTPUT)
    for spec, instances in metric_instances.items():
        instrument = output_instruments[spec]
        for instance in instances:
            # TODO(jishnu): Use context labels here
            labels = {label[0]: label[1] for label in instance.labels}
            _ = [instrument.record(val, labels)
                 for val in instance.metricValues]
