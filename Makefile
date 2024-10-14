.PHONY: venv code.deps
.DEFAULT_GOAL := all

all: venv code.deps

venv:
	@echo "+ $@"
	test -d .venv || python -m venv .venv

code.deps:
	@echo "+ $@"
	. .venv/bin/activate; pip install -Ur requirements.txt
