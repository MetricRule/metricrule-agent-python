"""Instruments used to record metrics.

Methods to initialize a single instrument given a specification, and a
set of instruments given a configuration, are provided.
"""
from typing import Any
import abc

import prometheus_client

from .mrmetric import MetricInstrumentSpec, MetricContext, get_instrument_specs
from ..config_gen.metric_configuration_pb2 import SidecarConfig  # pylint: disable=relative-beyond-top-level


class Instrument(abc.ABC):
    """Represents an instrument that can record a metric.
    """
    @abc.abstractmethod
    def record(self, value: Any, labels: dict[str, str]) -> None:
        """Associates the metric instrument with a value and labels.
        """


class Counter(Instrument):
    """Instrument that maintains a monotonically increasing count of a value.
    """

    def __init__(self, counter: prometheus_client.Counter):
        self.counter = counter

    def record(self, value: Any, labels: dict[str, str]) -> None:
        if len(labels) > 0:
            self.counter.labels(*[v for (_, v) in labels.items()]).inc(value)
        else:
            self.counter.inc(value)


class ValueRecorder(Instrument):
    """An instrument that records a value.
    """

    def __init__(self, recorder: prometheus_client.Histogram):
        self.recorder = recorder

    def record(self, value: Any, labels: dict[str, str]) -> None:
        if len(labels) > 0:
            self.recorder.labels(
                *[v for (_, v) in labels.items()]).observe(value)
        else:
            self.recorder.observe(value)


class NoOp(Instrument):
    """An instrument that does nothing.
    """

    def record(self, value: Any, labels: dict[str, str]) -> None:
        return None


def initialize_instrument(
    spec: MetricInstrumentSpec
) -> Instrument:
    """Initializes an instrument to the given spec.

    Args:
      spec: Specification of the instrument to create.

    Returns:
      The initialized instrument.
    """
    if spec.instrumentType == prometheus_client.Counter:
        counter = prometheus_client.Counter(
            name=spec.name,
            documentation='',
            labelnames=spec.labelNames)
        return Counter(counter)
    if spec.instrumentType == prometheus_client.Histogram:
        recorder = prometheus_client.Histogram(
            name=spec.name,
            documentation='',
            labelnames=spec.labelNames)
        return ValueRecorder(recorder)
    # TODO(jishnu): Add error logging.
    return NoOp()


def initialize_all_instruments(
    config: SidecarConfig
) -> dict[MetricContext, dict[MetricInstrumentSpec, Instrument]]:
    """Initializes all instruments specified by config.

    Args:
      config: A populated config proto.

    Returns:
      A map of specification to instruments, by context.
    """
    specs = get_instrument_specs(config)
    output = {}
    output[MetricContext.INPUT] = {
        spec: initialize_instrument(spec)
        for spec in specs[MetricContext.INPUT]
    }
    output[MetricContext.OUTPUT] = {
        spec: initialize_instrument(spec)
        for spec in specs[MetricContext.OUTPUT]
    }
    return output
