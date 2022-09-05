SHELL := /bin/bash

help:
	@echo "Available Commands:"
	@echo ""
	@echo "format: apply all available formatters"
	@echo ""
	@echo "test: run all tests"
	@echo ""
	@echo "update-examples: update outputs for every example directory"
	@echo ""


py_warn = PYTHONDEVMODE=1


# 'shopt -s globstar' allows us to run **/*.py globs. By default bash can't do recursive globs 
format:
	shopt -s globstar; \
	poetry run pyupgrade autograder/**/*.py --py37-plus --exit-zero-even-if-changed; \
	poetry run autoflake autograder --in-place --recursive --remove-all-unused-imports --ignore-init-module-imports --verbose; \
	poetry run isort autograder; \
	poetry run black autograder;

test:
	poetry run python3 test.py;

update-examples:
	bash update_examples.bash
