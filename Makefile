lint:
	black --check .
	flake8
	mypy ttt
	pylint ttt
test: lint
	pytest --cov
push: lint test
	git push
