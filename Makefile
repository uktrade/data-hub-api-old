.PHONY: venv install install-test requirements test

venv:
	virtualenv venv --python=python3
	. venv/bin/activate && pip install pip==8.1.1  # Pin pip to pip-tools required version

install:
	pip install -r requirements/base.txt

install-test:
	pip install -r requirements/testing.txt

requirements:
	$(MAKE) -C requirements clean all

# Pass some special flags which it's hard to get to work in `NOSE_ARGS`:
# * Ignore files: ignore apps.migrator.tests.models
# * Target tests: data-hub-api/apps, nose can't find the tests by default.
test:
	./manage.py test --settings=data-hub-api.settings.testing -I models.py -I __init__.py data-hub-api/apps
