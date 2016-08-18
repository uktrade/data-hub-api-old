.PHONY: all check clean

objects = base.in jenkins.in local.in production.in testing.in
outputs := $(objects:.in=.txt)
PIP_TOOLS_INSTALLED: ; @which pip-compile > /dev/null

all: $(outputs)

%.txt: %.in
	pip-compile -v --output-file $@ $<

# Record dependency tree for subfiles. This means that, for example, if base.in
# is updated, then all txt files will be recompiled on `all`.
jenkins.txt: testing.txt
local.txt: testing.txt
production.txt: base.txt
testing.txt: base.txt

check: PIP_TOOLS_INSTALLED

# Remove all compiled requirements files. Next `make all` will build *all*
# requirements to the latest version.
clean: check
	- rm *.txt
