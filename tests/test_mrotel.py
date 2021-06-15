from unittest import TestCase, main

import prometheus_client

from metricrule.agent.mrotel import initialize_instrument, Counter, ValueRecorder
from metricrule.agent.mrmetric import MetricInstrumentSpec


class TestMrOtel(TestCase):
    def test_initialize_counter(self):
        name = 'test_counter_init'
        spec = MetricInstrumentSpec(
            prometheus_client.Counter,
            int,
            name,
            (),
        )

        counter = initialize_instrument(spec)

        self.assertIsInstance(counter, Counter)
        # self.assertEqual(counter.counter, created_counter)

    def test_initialize_float_recorder(self):
        name = 'test_recorder_init'
        spec = MetricInstrumentSpec(
            prometheus_client.Histogram,
            float,
            name,
            (),
        )
        # meter.create_valuerecorder.return_value = created_recorder

        recorder = initialize_instrument(spec)

        self.assertIsInstance(recorder, ValueRecorder)
        # self.assertEqual(recorder.recorder, created_recorder)

    def test_counter_record(self):
        name = 'test_counter_record'
        spec = MetricInstrumentSpec(
            prometheus_client.Counter,
            int,
            name,
            (),
        )
        # meter.create_counter.return_value = created_counter
        counter = initialize_instrument(spec)

        counter.record(1, ())


if __name__ == '__main__':
    main()
