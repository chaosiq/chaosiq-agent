FROM python:3.8-alpine as cideps

RUN apk update && \
    apk add --virtual build-deps gcc g++ git libffi-dev linux-headers \
        python3-dev make musl-dev openssl-dev && \
    pip install -q -U pip

RUN adduser --disabled-password --home /home/svc svc
USER svc
WORKDIR /home/svc
COPY requirements.txt requirements.txt 
COPY requirements-dev.txt requirements-dev.txt 

RUN python3 -m venv .venv-build-and-test
RUN .venv-build-and-test/bin/pip install -U pip
RUN .venv-build-and-test/bin/pip install -r requirements.txt -r requirements-dev.txt
RUN python3 -m venv .venv-deploy
RUN .venv-deploy/bin/pip install -r requirements.txt

USER root
COPY . .
RUN chown svc:svc .
USER svc
RUN .venv-build-and-test/bin/pip install -e .
RUN .venv-build-and-test/bin/pylama chaosiqagent
RUN .venv-build-and-test/bin/pytest
RUN .venv-deploy/bin/pip install -U pip wheel && \
    .venv-deploy/bin/python setup.py bdist_wheel && \
    .venv-deploy/bin/pip install dist/*.whl


FROM python:3.8-alpine as cidelivery

RUN apk update && \
    rm -rf /tmp/* /root/.cache

RUN adduser --disabled-password --home /home/svc svc
USER svc
WORKDIR /home/svc
ENV PORT 8000
ENV BUCKET_CONFIG_PATH "${BUCKET_CONFIG_PATH}"

COPY LICENSE LICENSE
COPY --chown=svc:svc --from=cideps /home/svc/.venv-deploy .venv-deploy

ENTRYPOINT ["/bin/sh"]
CMD ["-c", ".venv-deploy/bin/chaosiqagent run --config ${BUCKET_CONFIG_PATH}"]
