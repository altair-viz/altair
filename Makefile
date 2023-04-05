all: install

install:
	python -m pip install -e .[dev,doc]

test :
	black --diff --color --check .
	ruff check .
	mypy altair tests
	python -m pytest --pyargs --doctest-modules tests

test-coverage:
	python -m pytest --pyargs --doctest-modules --cov=altair --cov-report term altair

test-coverage-html:
	python -m pytest --pyargs --doctest-modules --cov=altair --cov-report html altair
