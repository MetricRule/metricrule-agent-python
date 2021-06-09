from typing import Any, Optional, NamedTuple
from enum import Enum

from ..config_gen import metric_configuration_pb2

from opentelemetry import metrics
from jsonpath_ng import parse

class MetricInstrumentSpec(NamedTuple):
    instrumentType: type
    metricValueType: metrics.ValueT
    name: str

class MetricInstance(NamedTuple):
    metricValues: tuple[Any]
    labels: tuple[tuple[str, str]]

class MetricContext(Enum):
    UNKNOWN = 1
    INPUT = 2
    OUTPUT = 3

def get_instrument_specs(
        config: metric_configuration_pb2.SidecarConfig
    ) -> dict[MetricContext, tuple[MetricInstrumentSpec]]:
    specs = {}
    specs[MetricContext.INPUT] = tuple(map(_get_instrument_spec, config.input_metrics))
    specs[MetricContext.OUTPUT] = tuple(map(_get_instrument_spec, config.output_metrics))
    return specs

def get_metric_instances(
        config: metric_configuration_pb2.SidecarConfig,
        payload: Any,
        context: MetricContext,
    ) -> dict[MetricInstrumentSpec, tuple[MetricInstance]]:
    configs: tuple[metric_configuration_pb2.MetricConfig]
    filter: str
    if context == MetricContext.INPUT:
        configs = tuple(config.input_metrics)
        filter = _format_filter(config.input_content_filter)
    elif context == MetricContext.OUTPUT:
        configs = tuple(config.output_metrics)
        filter = _format_filter(config.output_content_filter)
    else:
        return {}

    filtered_values = (payload,)
    if len(filter) > 0:
        filtered_values = _get_filtered_values(filter, payload)

    outputs: dict[MetricInstrumentSpec, list[MetricInstance]] = {}
    for config in configs:
        for payload in filtered_values:
            values = _get_metric_values(config, payload)
            labels = _get_metric_labels(config, payload)
            spec = _get_instrument_spec(config)
            if spec in outputs:
                outputs[spec].append(MetricInstance(values, labels))
            else:
                outputs[spec] = [MetricInstance(values, labels)]
    return {spec:tuple(instances) for spec, instances in outputs.items()}

def get_context_labels(
        config: metric_configuration_pb2.SidecarConfig,
        payload: Any,
        context: MetricContext, 
    ) -> tuple[tuple[str, str]]:
    configs: tuple[metric_configuration_pb2.LabelConfig]
    filter: str
    if context == MetricContext.INPUT:
        configs = tuple(config.context_labels_from_input)
        filter = _format_filter(config.input_content_filter)
    elif context == MetricContext.OUTPUT:
        return ()
    else:
        return ()

    filtered_values = (payload,)
    if len(filter) > 0:
        filtered_values = _get_filtered_values(filter, payload)

    labels = []
    for config in configs:
        for payload in filtered_values:
            labels.extend(_get_labels_for_label_config(config, payload))
    return labels

def _format_filter(filter: str) -> str:
    if len(filter) > 0 and (filter[0] == '.' or filter[0] == '['):
        return '$' + filter
    return filter

def _get_instrument_spec(
        config: metric_configuration_pb2.MetricConfig,
    ) -> MetricInstrumentSpec:
    instrument_type = _get_instrument_type(config)
    metric_value_type = _get_metric_value_type(config)
    return MetricInstrumentSpec(
        instrumentType=instrument_type,
        metricValueType=metric_value_type,
        name=config.name,
    )

def _get_instrument_type(
        config: metric_configuration_pb2.MetricConfig,
    ) -> type:
    configured_type = config.WhichOneof('metric')
    if configured_type == 'simple_counter':
        return metrics.Counter
    elif configured_type == 'value':
        return metrics.ValueRecorder
    else:
        # default to counter.
        return metrics.Counter

def _get_metric_value_type(
        config: metric_configuration_pb2.MetricConfig,
    ) -> type:
    configured_type = config.WhichOneof('metric')
    if configured_type == 'simple_counter':
        return int
    elif configured_type == 'value':
        return float
    else:
        # default to counter.
        return int

def _get_filtered_values(
        filter: str,
        payload: Any,
    ) -> tuple[Any]:
    jsonpath_expr = parse(filter)
    values = [match.value for match in jsonpath_expr.find(payload)]
    return tuple(values)

def _get_metric_values(
        config: metric_configuration_pb2.MetricConfig,
        payload: Any,
    ) -> tuple[Any]:
    configured_type = config.WhichOneof('metric')
    if configured_type == 'simple_counter':
        return (1,)
    elif configured_type == 'value':
        return _extract_values(config.value.value, payload)
    # Default to a counter
    return (1,)

def _get_metric_labels(
        config: metric_configuration_pb2.MetricConfig,
        payload: Any,
    ) -> tuple[tuple[str, str]]:
    labels = []
    for label_config in config.labels:
        labels.extend(_get_labels_for_label_config(label_config, payload))
    return tuple(labels)

def _get_labels_for_label_config(
        config: metric_configuration_pb2.LabelConfig,
        payload: Any,
    ) -> tuple[tuple[str, str]]:
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
    ) -> tuple[Any]:
    if config.HasField('parsed_value'):
        value_type = config.parsed_value.parsed_type
        jsonpath_expr = parse(config.parsed_value.filter_path)
        matches = jsonpath_expr.find(payload)
        filtered = []
        for match in matches:
            filtered.append(_get_typed_value(match.value, value_type))
        return tuple(filtered)

    if config.HasField('static_value'):
        configured_static_type = config.WhichOneof('static_value')
        if configured_static_type == 'string_value':
            return (config.string_value,)
        elif configured_static_type == 'integer_value':
            return (config.integer_value,)
        elif configured_static_type == 'float_value':
            return (config.float_value,)

    return ()

def _get_typed_value(
        value: Any, 
        type: metric_configuration_pb2.ParsedValue.ParsedType,
    ) -> Optional[Any]:
    if type == metric_configuration_pb2.ParsedValue.FLOAT:
        return float(value)
    elif type == metric_configuration_pb2.ParsedValue.INTEGER:
        return int(value)
    elif type == metric_configuration_pb2.ParsedValue.STRING:
        return str(value)
    return None