lint:
	black --check .
	flake8
	mypy onx
	pylint onx
test: lint
	pytest --cov
release: test
	poetry version $(version)
	git commit -am 'Bumped the version'
	git tag $(poetry version -s)
	git push --tags
