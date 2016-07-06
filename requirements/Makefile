objects = base.in production.in testing.in local.in jenkins.in  # In order of dependency
outputs := $(objects:.in=.txt)
PIP_TOOLS_INSTALLED: ; @which pip-compile > /dev/null

all: $(outputs)

%.txt: %.in
	pip-compile -v --output-file $@ $<

check: PIP_TOOLS_INSTALLED

clean: check
	- rm *.txt
