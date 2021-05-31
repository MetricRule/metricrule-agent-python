from typing import Any, Optional
import abc

from opentelemetry import metrics

from . import mrmetric

class Instrument(abc.ABC):
    @abc.abstractmethod
    def record(self, value: Any) -> Optional[tuple[metrics.Metric, Any]]:
        """
        Associates the metric instrument with a value.
        The tuple is expected to be used in meter.record_batch
        """

class Counter(Instrument):
    def __init__(self, counter: metrics.Counter):
        self.counter = counter

    def record(self, value: Any) -> Optional[tuple[metrics.Metric, Any]]:
        return (self.counter, value)

class ValueRecorder(Instrument):
    def __init__(self, recorder: metrics.ValueRecorder):
        self.recorder = recorder

    def record(self, value: Any) -> Optional[tuple[metrics.Metric, Any]]:
        return (self.recorder, value)

class NoOp(Instrument):
    def record(self, _: Any) -> Optional[tuple[metrics.Metric, Any]]:
        return None

def initialize_instrument(
        meter: metrics.Meter, 
        spec: mrmetric.MetricInstrumentSpec
    ) -> Instrument:
    if spec.instrumentType == metrics.Counter:
        counter = meter.create_counter(
            name=spec.name,
            description='',
            unit='',
            value_type=spec.metricValueType,
        )
        return Counter(counter)
    elif spec.instrumentType == metrics.ValueRecorder:
        recorder = meter.create_valuerecorder(
            name=spec.name,
            description='',
            unit='',
            value_type=spec.metricValueType
        )
        return ValueRecorder(recorder)
    # TODO(jishnu): Add error logging.
    return NoOp()
