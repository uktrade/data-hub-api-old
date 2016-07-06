FROM python:3.5.1

RUN apt-get -y install \
    gcc \
    libc-dev \
    libpq-dev

RUN pip3 install -U setuptools pip wheel

COPY ./requirements /requirements
RUN pip3 install -r /requirements/jenkins.txt

COPY . /app
WORKDIR /app

ADD . /app
