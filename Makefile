all: config

DOCKER_BUILDKIT=1

.PHONY: config
config:
	@make py-proto -C api/
	@mkdir -p src/metricrule/config_gen
	@mv api/proto/*.py src/metricrule/config_gen
	@touch src/metricrule/config_gen/__init__.py
	@printf "__all__ = ['proto_pb2']" > src/metricrule/config_gen/__init__.py

.PHONY: unit-test
unit-test:
	@docker build . --target unit-test

.PHONY: lint
lint:
	@docker build . --target lint

.PHONY: type-check
type-check:
	@docker build . --target type-check