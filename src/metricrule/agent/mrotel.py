'''
This module defines OpenTelemetry instruments used to record metrics.

An `initialize_instrument` method is also provided that initializes an
appropriate instrument given a specification.
'''
from typing import Any, Optional
import abc
from opentelemetry import metrics
from opentelemetry.metrics import Meter, Metric

from .mrmetric import MetricInstrumentSpec


class Instrument(abc.ABC):
    '''
    Represents an instrument that can record a metric.
    '''
    @abc.abstractmethod
    def record(self, value: Any) -> Optional[tuple[Metric, Any]]:
        '''
        Associates the metric instrument with a value.
        The tuple is expected to be used in meter.record_batch.
        '''


class Counter(Instrument):
    '''
    An instrument that maintains an increasing count of a value.
    '''

    def __init__(self, counter: metrics.Counter):
        self.counter = counter

    def record(self, value: Any) -> Optional[tuple[Metric, Any]]:
        return (self.counter, value)


class ValueRecorder(Instrument):
    '''
    An instrument that records a value.
    '''

    def __init__(self, recorder: metrics.ValueRecorder):
        self.recorder = recorder

    def record(self, value: Any) -> Optional[tuple[Metric, Any]]:
        return (self.recorder, value)


class NoOp(Instrument):
    '''
    An instrument that does not do anything.
    '''

    def record(self, _: Any) -> Optional[tuple[Metric, Any]]:
        return None


def initialize_instrument(
    meter: Meter,
    spec: MetricInstrumentSpec
) -> Instrument:
    '''
    Initializes an instrument to the given spec in the given meter.
    '''
    if spec.instrumentType == metrics.Counter:
        counter = meter.create_counter(
            name=spec.name,
            description='',
            unit='',
            value_type=spec.metricValueType,
        )
        return Counter(counter)
    if spec.instrumentType == metrics.ValueRecorder:
        recorder = meter.create_valuerecorder(
            name=spec.name,
            description='',
            unit='',
            value_type=spec.metricValueType
        )
        return ValueRecorder(recorder)
    # TODO(jishnu): Add error logging.
    return NoOp()
