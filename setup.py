import sys
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py


class Build(build_py):
    """Customized setuptools build command - builds protos on build."""

    def run(self):
        protoc_command = ["make", "config"]
        if subprocess.call(protoc_command) != 0:
            sys.exit(-1)
        build_py.run(self)


setup(
    cmdclass={
        'build_py': Build,
    }
)
