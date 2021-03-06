# syntax=docker/dockerfile:1.2

FROM --platform=${BUILDPLATFORM:-linux/amd64} python:3.9-buster AS base

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive \
    apt-get install --no-install-recommends --assume-yes \
      protobuf-compiler

COPY . .
RUN pip install .

FROM base AS type-check
RUN pip install mypy types-protobuf
RUN mypy src/metricrule/agent

FROM base AS lint
RUN pip install pylint
RUN pylint src/metricrule/agent

FROM base AS unit-test
RUN python -m unittest


