.PHONY: venv install install-test requirements test

venv:
	virtualenv venv --python=python3.5

install:
	pip install -r requirements/base.txt

install-test:
	pip install -r requirements/testing.txt

requirements:
	$(MAKE) -C requirements all

# Pass some special flags which it's hard to get to work in `NOSE_ARGS`:
# * Ignore files: ignore apps.migrator.tests.models
# * Target tests: data-hub-api/apps, nose can't find the tests by default.
test:
	./manage.py test --settings=data-hub-api.settings.testing -I models.py -I __init__.py data-hub-api/apps -v 2

lint:
	flake8 data-hub-api
