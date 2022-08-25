lint:
	black ttt
	black ttt.py
	mypy ttt
	pylint ttt
test: lint
	pytest --cov
push: lint test
	git push
