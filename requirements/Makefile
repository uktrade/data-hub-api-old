objects = base.in production.in testing.in local.in jenkins.in  # In order of dependency
outputs := $(objects:.in=.txt)

all: $(outputs)

%.txt: %.in
	pip-compile -v --output-file $@ $<

clean:
	- rm *.txt
