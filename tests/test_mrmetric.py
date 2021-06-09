from unittest import TestCase, main

from google.protobuf import text_format
from opentelemetry import metrics

from metricrule.agent import mrmetric
from metricrule.config_gen import metric_configuration_pb2
from metricrule.agent.mrmetric import *

class TestMrMetric(TestCase):
    def test_input_counter_instrument_spec(self):
        config_data = """
        input_metrics {
            name: "simple"
            simple_counter: {}
        }
        """
        config_proto = metric_configuration_pb2.SidecarConfig()
        text_format.Parse(config_data, config_proto)

        spec = get_instrument_specs(config_proto)

        self.assertEqual(len(spec[MetricContext.INPUT]), 1)
        self.assertEqual(len(spec[MetricContext.OUTPUT]), 0)

        single_spec = spec[MetricContext.INPUT][0]
        self.assertEqual(single_spec.instrumentType, metrics.Counter)
        self.assertEqual(single_spec.metricValueType, int)
        self.assertEqual(single_spec.name, 'simple')

    def test_input_counter_metrics(self):
        config_data = """
        input_metrics {
            name: "simple"
            simple_counter: {}
        }
        """
        config_proto = metric_configuration_pb2.SidecarConfig()
        text_format.Parse(config_data, config_proto)

        result = get_metric_instances(config_proto, '{}', MetricContext.INPUT)

        expected_length = 1
        self.assertEqual(len(result), expected_length)
        counter = 0
        for spec, instances in result.items():
            counter += 1
            if counter > expected_length:
                self.fail("Exceeded expected iteration length")
            
            self.assertEqual(spec.instrumentType, metrics.Counter)
            self.assertEqual(spec.metricValueType, int)
            self.assertEqual(spec.name, 'simple')

            self.assertEqual(len(instances), 1)
            instance = instances[0]
            self.assertEqual(len(instance.labels), 0)
            self.assertEqual(len(instance.metricValues), 1)
            value = instance.metricValues[0]
            self.assertEqual(value, 1)

    def test_input_counter_with_labels(self):
        pass

    def test_output_value_metrics(self):
        pass

    def test_output_nested_value_metrics(self):
        pass

    def test_multiple_inputs_nested_value_metrics(self):
        pass

    def test_get_input_context_labels(self):
        pass

    def test_multiple_labels_with_wildcard(self):
        pass

    def test_multiple_labels_with_filter(self):
        pass

    def test_get_input_context_labels_with_filter(self):
        pass

    def test_get_output_values_with_filter_metrics(self):
        pass

    def test_input_counter_multiple_filter_metrics(self):
        pass

if __name__ == '__main__':
    main()