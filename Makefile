lint:
	black --check .
	flake8
	mypy onx
	pylint onx
test: lint
	pytest --cov
