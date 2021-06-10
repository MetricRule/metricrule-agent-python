import json
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
        payload = json.loads('{}')

        result = get_metric_instances(config_proto, payload, MetricContext.INPUT)

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
        config_data = """
        input_metrics {
            name: "simple"
            simple_counter: {}
            labels: {
                label_key: { string_value: "Application" }
                label_value: { string_value: "MetricRule" }
            }
        }
        """
        config_proto = metric_configuration_pb2.SidecarConfig()
        text_format.Parse(config_data, config_proto)
        payload = json.loads('{}')

        result = get_metric_instances(config_proto, payload, MetricContext.INPUT)

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
            self.assertEqual(len(instance.labels), 1)
            label = instance.labels[0]
            self.assertEqual(label[0], 'Application')
            self.assertEqual(label[1], 'MetricRule')
            self.assertEqual(len(instance.metricValues), 1)
            value = instance.metricValues[0]
            self.assertEqual(value, 1)

    def test_output_value_metrics(self):
        config_data = """
        output_metrics {
            name: "output_values"
            value {
                value {
                    parsed_value {
                        field_path: "$.prediction"
                        parsed_type: FLOAT
                    }
                }
            }
        }
        """
        config_proto = metric_configuration_pb2.SidecarConfig()
        text_format.Parse(config_data, config_proto)
        payload = json.loads('{ "prediction": 0.495 }')

        result = get_metric_instances(config_proto, payload, MetricContext.OUTPUT)

        expected_length = 1
        self.assertEqual(len(result), expected_length)
        counter = 0
        for spec, instances in result.items():
            counter += 1
            if counter > expected_length:
                self.fail("Exceeded expected iteration length")
            
            self.assertEqual(spec.instrumentType, metrics.ValueRecorder)
            self.assertEqual(spec.metricValueType, float)
            self.assertEqual(spec.name, 'output_values')

            self.assertEqual(len(instances), 1)
            instance = instances[0]
            self.assertEqual(len(instance.labels), 0)
            self.assertEqual(len(instance.metricValues), 1)
            value = instance.metricValues[0]
            self.assertEqual(value, 0.495)

    def test_output_nested_value_metrics(self):
        config_data = """
        output_metrics {
            name: "output_values"
            value {
                value {
                    parsed_value {
                        field_path: "$.prediction[0][0]"
                        parsed_type: FLOAT
                    }
                }
            }
        }
        """
        config_proto = metric_configuration_pb2.SidecarConfig()
        text_format.Parse(config_data, config_proto)
        payload = json.loads('{ "prediction": [[0.495]] }')

        result = get_metric_instances(config_proto, payload, MetricContext.OUTPUT)

        expected_length = 1
        self.assertEqual(len(result), expected_length)
        counter = 0
        for spec, instances in result.items():
            counter += 1
            if counter > expected_length:
                self.fail("Exceeded expected iteration length")
            
            self.assertEqual(spec.instrumentType, metrics.ValueRecorder)
            self.assertEqual(spec.metricValueType, float)
            self.assertEqual(spec.name, 'output_values')

            self.assertEqual(len(instances), 1)
            instance = instances[0]
            self.assertEqual(len(instance.labels), 0)
            self.assertEqual(len(instance.metricValues), 1)
            value = instance.metricValues[0]
            self.assertEqual(value, 0.495)

    def test_multiple_inputs_nested_value_metrics(self):
        config_data = """
        input_metrics {
            name: "input_distribution_counts"
            simple_counter {}
            labels {
                label_key { string_value: "PetType" }
                label_value {
                    parsed_value {
                        field_path: ".instances[0].Type[0]"
                        parsed_type: STRING
                    }
                }
            }
            labels {
                label_key { string_value: "Breed" }
                label_value {
                    parsed_value {
                        field_path: ".instances[0].Breed1[0]"
                        parsed_type: STRING
                    }
                }
            }
        } 
        """
        config_proto = metric_configuration_pb2.SidecarConfig()
        text_format.Parse(config_data, config_proto)
        payload = json.loads("""{"instances": [{
            "Type": [
                "Cat"
            ],
            "Age": [
                4
            ],
            "Breed1": [
                "Turkish"
            ]
        }]}""")

        result = get_metric_instances(config_proto, payload, MetricContext.INPUT)

        expected_length = 1
        self.assertEqual(len(result), expected_length)
        counter = 0
        for spec, instances in result.items():
            counter += 1
            if counter > expected_length:
                self.fail("Exceeded expected iteration length")
            
            self.assertEqual(spec.instrumentType, metrics.Counter)
            self.assertEqual(spec.metricValueType, int)
            self.assertEqual(spec.name, 'input_distribution_counts')

            self.assertEqual(len(instances), 1)
            instance = instances[0]

            self.assertEqual(len(instance.metricValues), 1)
            value = instance.metricValues[0]
            self.assertEqual(value, 1)

            self.assertEqual(len(instance.labels), 2)
            self.assertEqual(instance.labels[0][0], 'PetType')
            self.assertEqual(instance.labels[0][1], 'Cat')
            self.assertEqual(instance.labels[1][0], 'Breed')
            self.assertEqual(instance.labels[1][1], 'Turkish')

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