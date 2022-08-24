lint:
	black noughts_and_crosses
	mypy noughts_and_crosses
	pylint noughts_and_crosses
test:
	pytest --cov
push: lint test
	git push
