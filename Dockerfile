FROM python:3.7.6-alpine3.11

ENV LANG C.UTF-8
ENV HOME /root
ENV SAM_CLI_TELEMETRY=0

RUN apk add --no-cache python py-pip && \
    apk add --no-cache gcc python-dev musl-dev && \
    pip --disable-pip-version-check install \
        boto3 botocore awscli aws-sam-cli && \
    apk -v --purge --no-cache del gcc python-dev musl-dev && \
    apk add --no-cache git openssh && \
    pip3 install jinja2 coverage

RUN mkdir /root/app

RUN apk add --no-cache docker bash

WORKDIR /root/app