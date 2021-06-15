'''
This module defines OpenTelemetry instruments used to record metrics.

An `initialize_instrument` method is also provided that initializes an
appropriate instrument given a specification.
'''
from typing import Any
import abc

import prometheus_client

from .mrmetric import MetricInstrumentSpec


class Instrument(abc.ABC):
    '''
    Represents an instrument that can record a metric.
    '''
    @abc.abstractmethod
    def record(self, value: Any, labels: tuple[tuple[str, str]]) -> None:
        '''
        Associates the metric instrument with a value and labels.
        '''


class Counter(Instrument):
    '''
    An instrument that maintains a monotonically increasing count of a value.
    '''

    def __init__(self, counter: prometheus_client.Counter):
        self.counter = counter

    def record(self, value: Any, labels: dict[str, str]) -> None:
        if len(labels) > 0:
            self.counter.labels(*[v for (_, v) in labels.items()]).inc(value)
        else:
            self.counter.inc(value)


class ValueRecorder(Instrument):
    '''
    An instrument that records a value.
    '''

    def __init__(self, recorder: prometheus_client.Histogram):
        self.recorder = recorder

    def record(self, value: Any, labels: dict[str, str]) -> None:
        if len(labels) > 0:
            self.recorder.labels(
                *[v for (_, v) in labels.items()]).observe(value)
        else:
            self.recorder.observe(value)


class NoOp(Instrument):
    '''
    An instrument that does not do anything.
    '''

    def record(self, value: Any, labels: dict[str, str]) -> None:
        return None


def initialize_instrument(
    spec: MetricInstrumentSpec
) -> Instrument:
    '''
    Initializes an instrument to the given spec in the given meter.
    '''
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
