all: config

.PHONY: config
config:
	@make py-proto -C api/
	@mkdir -p src/metricrule/config_gen
	@mv api/proto/*.py src/metricrule/config_gen
	@touch src/metricrule/config_gen/__init__.py
	@printf "__all__ = ['proto_pb2']" > src/metricrule/config_gen/__init__.py
