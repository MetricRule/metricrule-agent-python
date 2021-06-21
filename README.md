# 📏 MetricRule

Easy open source monitoring for ML models.

> Agents for monitoring Python webservers - e.g Flask, Django, FastAPI running ML models.

[![Continuous Integration](https://github.com/MetricRule/metricrule-agent-python/actions/workflows/ci.yaml/badge.svg)](https://github.com/MetricRule/metricrule-agent-python/actions/workflows/ci.yaml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

----

## Motivation

MetricRule agents are designed to be deployed with a serving model endpoint to generate input feature and output distribution metrics based on the model's endpoint usage. Integrations with Python WSGI and ASGI servers, like Django, Flask and FastAPI are supported.

The motivation of this project is to make it easier to monitor feature distributions in production to better catch real world ML issues like training-serving skew, feature drifts, poor model performance on specific slices of input.

## Examples

Please see the [example](example) directory to see usages.

## For more information

Please refer to [metricrule.com](https://www.metricrule.com) for more information.
