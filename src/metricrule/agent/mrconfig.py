"""Utils for dealing with agent configuration.

Provides a method to read a protoconf file from a file path into a proto.
"""
from google.protobuf import text_format

from ..config_gen.metric_configuration_pb2 import SidecarConfig  # pylint: disable=relative-beyond-top-level


def load_config(config_path: str) -> SidecarConfig:
    """Loads a file from the specified path into a config proto.

    Args:
      config_path: Path to a textproto config file.

    Returns:
      A config proto populated with the values read from the file.
    """
    config_data = ''
    if len(config_path) > 0:
        with open(config_path, 'r') as config_file:
            config_data = config_file.read()
    config_proto = SidecarConfig()
    text_format.Parse(config_data, config_proto)
    return config_proto
