.PHONY: venv install install-test requirements

venv:
	virtualenv venv --python=python3
	. venv/bin/activate && pip install pip==8.1.1  # Pin pip to pip-tools required version

install:
	pip install -r requirements/base.txt

install-test:
	pip install -r requirements/testing.txt

requirements:
	$(MAKE) -C requirements clean all
