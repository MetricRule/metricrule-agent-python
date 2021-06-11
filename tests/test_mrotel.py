from unittest import TestCase, main
from unittest.mock import MagicMock, Mock

from opentelemetry import metrics

from metricrule.agent.mrotel import initialize_instrument, Counter, ValueRecorder
from metricrule.agent.mrmetric import MetricInstrumentSpec


class TestMrOtel(TestCase):
    def test_initialize_counter(self):
        meter = MagicMock(metrics.Meter)
        created_counter = Mock(Counter)
        name = 'test_counter_init'
        spec = MetricInstrumentSpec(
            metrics.Counter,
            int,
            name,
        )
        meter.create_counter.return_value = created_counter

        counter = initialize_instrument(meter, spec)

        meter.create_counter.assert_called_with(
            name=name,
            description='',
            unit='',
            value_type=int)
        self.assertIsInstance(counter, Counter)
        self.assertEqual(counter.counter, created_counter)

    def test_initialize_float_recorder(self):
        meter = MagicMock(metrics.Meter)
        created_recorder = Mock(Counter)
        name = 'test_recorder_init'
        spec = MetricInstrumentSpec(
            metrics.ValueRecorder,
            float,
            name,
        )
        meter.create_valuerecorder.return_value = created_recorder

        recorder = initialize_instrument(meter, spec)

        meter.create_valuerecorder.assert_called_with(
            name=name,
            description='',
            unit='',
            value_type=float)
        self.assertIsInstance(recorder, ValueRecorder)
        self.assertEqual(recorder.recorder, created_recorder)

    def test_counter_record(self):
        meter = MagicMock(metrics.Meter)
        created_counter = Mock(Counter)
        name = 'test_counter_init'
        spec = MetricInstrumentSpec(
            metrics.Counter,
            int,
            name,
        )
        meter.create_counter.return_value = created_counter
        counter = initialize_instrument(meter, spec)

        recording = counter.record(1)

        self.assertIsInstance(recording, tuple)
        self.assertEqual(len(recording), 2)
        self.assertEqual(recording[0], created_counter)
        self.assertEqual(recording[1], 1)


if __name__ == '__main__':
    main()
