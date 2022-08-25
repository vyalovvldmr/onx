lint:
	black ttt
	mypy ttt
	pylint ttt
test:
	pytest --cov
push: lint test
	git push
