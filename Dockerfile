FROM python:3.8-alpine as cideps

RUN apk update && \
    apk add --virtual build-deps gcc g++ git libffi-dev linux-headers \
        python3-dev make musl-dev openssl-dev && \
    pip install -q -U pip

RUN addgroup --gid 1001 svc
RUN adduser --disabled-password --home /home/svc --uid 1001 --ingroup svc svc
USER svc
WORKDIR /home/svc
COPY requirements.txt requirements.txt

RUN python3 -m venv .venv-deploy
RUN .venv-deploy/bin/pip install -r requirements.txt

USER root
COPY . .
RUN chown svc:svc .
USER svc
RUN .venv-deploy/bin/pip install -U pip wheel && \
    .venv-deploy/bin/python setup.py bdist_wheel && \
    .venv-deploy/bin/pip install dist/*.whl


FROM python:3.8-alpine as cidelivery

RUN apk update && \
    rm -rf /tmp/* /root/.cache

# Any non-zero number will do, and unfortunately a named user will not,
# as k8s pod securityContext runAsNonRoot can't resolve the user ID:
# https://github.com/kubernetes/kubernetes/issues/40958
RUN addgroup --gid 1001 svc
RUN adduser --disabled-password --home /home/svc --uid 1001 --ingroup svc svc
USER 1001
WORKDIR /home/svc
ENV PORT 8000

COPY LICENSE LICENSE
COPY --chown=svc:svc --from=cideps /home/svc/.venv-deploy .venv-deploy

ENTRYPOINT ["/bin/sh"]
CMD ["-c", ".venv-deploy/bin/chaosiq-agent run --config /etc/chaosiq/agent/.env"]
