"""Recorder of metrics for request and response payloads.


"""
import json
from typing import MutableSequence, Optional, Union

from ..config_gen.metric_configuration_pb2 import SidecarConfig  # pylint: disable=relative-beyond-top-level
from .mrmetric import get_context_labels, get_metric_instances, MetricContext, MetricInstrumentSpec
from .mrotel import Instrument

InstrumentMap = dict[MetricInstrumentSpec, Instrument]
MutableLabelSequence = Optional[MutableSequence[tuple[tuple[str, str], ...]]]


def log_request_metrics(config: SidecarConfig,
                        input_instruments: InstrumentMap,
                        request_body: Union[str, bytes],
                        context_label_sink: MutableLabelSequence = None) -> None:
    """Logs metrics for a request payload.

    Args:
      config: A populated config proto.
      input_instruments: A map of instrument specifications to their
        equivalent initialized instruments.
      request_body: Content of the request payload received.
      context_label_sink: A mutable sequence to which any context labels
        will be appended.
    """
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
    if context_label_sink is not None:
        context_label_sink.append(context_labels)


def log_response_metrics(config: SidecarConfig,
                         output_instruments: InstrumentMap,
                         response_body: Union[str, bytes],
                         context_label_source: MutableLabelSequence = None) -> None:
    """Logs metrics for a response payload.

    Args:
      config: A populated config proto.
      output_instruments: A map of instrument specifications to their
        equivalent initialized instruments.
      response_body: Content of the response payload sent.
      context_label_source: A mutable source from which any context labels
        will be popped.
    """
    try:
        json_obj = json.loads(response_body)
    except ValueError:
        return
    metric_instances = get_metric_instances(
        config, json_obj, MetricContext.OUTPUT)
    for spec, instances in metric_instances.items():
        instrument = output_instruments[spec]
        for instance in instances:
            labels = {label[0]: label[1] for label in instance.labels}
            if context_label_source is not None and len(context_label_source) > 0:
                context_labels = context_label_source.pop()
                labels.update({label[0]: label[1] for label in context_labels})
            _ = [instrument.record(val, labels)
                 for val in instance.metricValues]
