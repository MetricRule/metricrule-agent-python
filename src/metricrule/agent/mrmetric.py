"""Module to generate metric specifications and instances.

This module provides three functions:
  - get_instrument_specs to specify metric instruments from config.
  - get_metric_instances to generate instances / values of metrics,
      given a config and data.
  - get_context_labels to generate metric labels, given config and
       data.
"""
from typing import Any, Optional, NamedTuple
from enum import Enum

from jsonpath_ng import parse
import prometheus_client

from ..config_gen import metric_configuration_pb2  # pylint: disable=relative-beyond-top-level


class MetricInstrumentSpec(NamedTuple):
    """Specification to identify an instrument to collect metrics.

    Attributes:
      instrumentType: The type of instrument (e.g counter, histogram).
      metricValueType: The type of value recorder (e.g int, float).
      name: The name of the instrument.
      labelNames: A list of label names associated with the instrument.
    """
    instrumentType: type
    metricValueType: type
    name: str
    labelNames: tuple[str, ...]


class MetricInstance(NamedTuple):
    """A specific instance of a metric recording.

    Attributes:
        metricValues: A sequence of values to record.
        labels: A sequence of key-value pairs associated with the recording.
    """
    metricValues: tuple[Any, ...]
    labels: tuple[tuple[str, str], ...]


class MetricContext(Enum):
    """Enumerations of contexts metrics can be in.
    """
    UNKNOWN = 1
    INPUT = 2
    OUTPUT = 3


def get_instrument_specs(
    config: metric_configuration_pb2.SidecarConfig
) -> dict[MetricContext, tuple[MetricInstrumentSpec, ...]]:
    """Gets instrument specifications needed for a configuration.

    Args:
      config: A populated config proto.

    Returns:
      Instrument specifications, mapped to the context they should
      be used in.
    """
    specs = {}

    def get_spec_fn(metric_config: metric_configuration_pb2.MetricConfig):
        return _get_instrument_spec(metric_config, config.context_labels_from_input)
    specs[MetricContext.INPUT] = tuple(
        map(get_spec_fn, config.input_metrics))
    specs[MetricContext.OUTPUT] = tuple(
        map(get_spec_fn, config.output_metrics))
    return specs


def get_metric_instances(
    config: metric_configuration_pb2.SidecarConfig,
    payload: Any,
    context: MetricContext,
) -> dict[MetricInstrumentSpec, tuple[MetricInstance, ...]]:
    """Gets metric instances to record.

    Args:
      config: A populated config proto.
      payload: Data based on which to generate metrics.
      context: The metric context to generate metrics for.

    Returns:
      A mapping of instrument specifications to a sequence of
      generated metric instances.
    """
    configs: tuple[metric_configuration_pb2.MetricConfig, ...]
    filter_str: str
    ctx_labels_for_spec: tuple[metric_configuration_pb2.LabelConfig, ...]
    if context == MetricContext.INPUT:
        configs = tuple(config.input_metrics)
        filter_str = _format_filter(config.input_content_filter)
        ctx_labels_for_spec = config.context_labels_from_input
    elif context == MetricContext.OUTPUT:
        configs = tuple(config.output_metrics)
        filter_str = _format_filter(config.output_content_filter)
        ctx_labels_for_spec = config.context_labels_from_input
    else:
        return {}

    filtered_values: tuple[Any, ...] = (payload,)
    if len(filter_str) > 0:
        filtered_values = _get_filtered_values(filter_str, payload)

    outputs: dict[MetricInstrumentSpec, list[MetricInstance]] = {}
    for metric_config in configs:
        for filtered_payload in filtered_values:
            values = _get_metric_values(metric_config, filtered_payload)
            labels = _get_metric_labels(metric_config, filtered_payload)
            spec = _get_instrument_spec(metric_config, ctx_labels_for_spec)
            if spec in outputs:
                outputs[spec].append(MetricInstance(values, labels))
            else:
                outputs[spec] = [MetricInstance(values, labels)]
    return {spec: tuple(instances) for spec, instances in outputs.items()}


def get_context_labels(
    config: metric_configuration_pb2.SidecarConfig,
    payload: Any,
    context: MetricContext,
) -> tuple[tuple[str, str], ...]:
    """Gets context labels to attach to metrics.

    Args:
      config: A populated config proto.
      payload: Data based on which to generate labels.
      context: The metric context to generate labels for.

    Returns:
      A list of key-value pairs of the labels to attach.
    """
    configs: tuple[metric_configuration_pb2.LabelConfig, ...]
    filter_str: str
    if context == MetricContext.INPUT:
        configs = tuple(config.context_labels_from_input)
        filter_str = _format_filter(config.input_content_filter)
    elif context == MetricContext.OUTPUT:
        return ()
    else:
        return ()

    filtered_values: tuple[Any, ...] = (payload,)
    if len(filter_str) > 0:
        filtered_values = _get_filtered_values(filter_str, payload)

    labels: list[tuple[str, str]] = []
    for label_config in configs:
        for filtered_payload in filtered_values:
            labels.extend(_get_labels_for_label_config(
                label_config, filtered_payload))
    return tuple(labels)


def _format_filter(filter_str: str) -> str:
    if len(filter_str) > 0 and (filter_str[0] == '.' or filter_str[0] == '['):
        return '$' + filter_str
    return filter_str


def _get_instrument_spec(
    config: metric_configuration_pb2.MetricConfig,
    context_labels: tuple[metric_configuration_pb2.LabelConfig, ...] = ()
) -> MetricInstrumentSpec:
    instrument_type = _get_instrument_type(config)
    metric_value_type = _get_metric_value_type(config)
    label_names = _get_metric_label_keys_no_payload(
        config) + _label_keys_no_payload(context_labels)

    return MetricInstrumentSpec(
        instrumentType=instrument_type,
        metricValueType=metric_value_type,
        name=config.name,
        labelNames=label_names,
    )


def _get_instrument_type(
    config: metric_configuration_pb2.MetricConfig,
) -> type:
    configured_type = config.WhichOneof('metric')
    if configured_type == 'simple_counter':
        return prometheus_client.Counter
    if configured_type == 'value':
        return prometheus_client.Histogram
    # default to counter.
    return prometheus_client.Counter


def _get_metric_value_type(
    config: metric_configuration_pb2.MetricConfig,
) -> type:
    configured_type = config.WhichOneof('metric')
    if configured_type == 'simple_counter':
        return int
    if configured_type == 'value':
        return float
    # default to counter.
    return int


def _get_filtered_values(
    filter_str: str,
    payload: Any,
) -> tuple[Any, ...]:
    jsonpath_expr = parse(filter_str)
    values = [match.value for match in jsonpath_expr.find(payload)]
    return tuple(values)


def _get_metric_values(
    config: metric_configuration_pb2.MetricConfig,
    payload: Any,
) -> tuple[Any, ...]:
    configured_type = config.WhichOneof('metric')
    if configured_type == 'simple_counter':
        return (1,)
    if configured_type == 'value':
        return _extract_values(config.value.value, payload)
    # Default to a counter
    return (1,)


def _get_metric_labels(
    config: metric_configuration_pb2.MetricConfig,
    payload: Any,
) -> tuple[tuple[str, str], ...]:
    labels: list[tuple[str, str]] = []
    for label_config in config.labels:
        labels.extend(_get_labels_for_label_config(label_config, payload))
    return tuple(labels)


def _get_metric_label_keys_no_payload(
    config: metric_configuration_pb2.MetricConfig
) -> tuple[str, ...]:
    return _label_keys_no_payload(config.labels)


def _label_keys_no_payload(
    configs: tuple[metric_configuration_pb2.LabelConfig, ...]
) -> tuple[str, ...]:
    label_keys: list[str] = []
    for label_config in configs:
        key = _extract_values(label_config.label_key, {})
        label_keys.extend(key)
    return tuple(label_keys)


def _get_labels_for_label_config(
    config: metric_configuration_pb2.LabelConfig,
    payload: Any,
) -> tuple[tuple[str, str], ...]:
    keys = _extract_values(config.label_key, payload)
    values = _extract_values(config.label_value, payload)
    iterlen = max(len(keys), len(values))
    results = []
    if len(keys) == 0 or len(values) == 0:
        return ()
    for i in range(iterlen):
        key = keys[i % len(keys)]
        value = values[i % len(values)]
        results.append((key, value))
    return tuple(results)


def _extract_values(
    config: metric_configuration_pb2.ValueConfig,
    payload: Any,
) -> tuple[Any, ...]:
    if config.HasField('parsed_value'):
        value_type = config.parsed_value.parsed_type
        filter_str = _format_filter(config.parsed_value.field_path)
        jsonpath_expr = parse(filter_str)
        matches = jsonpath_expr.find(payload)
        filtered = []
        for match in matches:
            filtered.append(_get_typed_value(match.value, value_type))
        return tuple(filtered)

    if config.HasField('static_value'):
        configured_static_type = config.WhichOneof('static_value')
        if configured_static_type == 'string_value':
            return (config.string_value,)
        if configured_static_type == 'integer_value':
            return (config.integer_value,)
        if configured_static_type == 'float_value':
            return (config.float_value,)

    return ()


def _get_typed_value(
    value: Any,
    parsed_type: metric_configuration_pb2.ParsedValue.ParsedType,
) -> Optional[Any]:
    if parsed_type == metric_configuration_pb2.ParsedValue.FLOAT:
        return float(value)
    if parsed_type == metric_configuration_pb2.ParsedValue.INTEGER:
        return int(value)
    if parsed_type == metric_configuration_pb2.ParsedValue.STRING:
        return str(value)
    return None
