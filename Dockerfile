FROM python:3.5.1

ENV DJANGO__TEST_INTEGRATION false
ENV DJANGO__CDMS_BASE_URL https://example.com
ENV DJANGO__CDMS_USERNAME username
ENV DJANGO__CDMS_PASSWORD password
ENV DJANGO__DB_USERNAME postgres
ENV DJANGO__DB_PASSWORD postgres
ENV DJANGO__DB_HOST db
ENV DJANGO__DB_PORT 5432

COPY ./requirements /requirements

RUN apt-get -y install gcc libc-dev libpq-dev && \
      pip3 install -U setuptools pip wheel && \
      pip3 install -r /requirements/testing.txt

COPY . /app
WORKDIR /app
