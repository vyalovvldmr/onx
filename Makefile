lint:
	black --check .
	flake8
	mypy onx
	pylint onx
test: lint
	pytest --cov
push: lint test
	git push
