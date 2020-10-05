# ChaosIQ Agent for running Chaos Toolkit experiments

[![Build Status](https://github.com/chaosiq/chaosiq-agent/workflows/CI/badge.svg)](https://github.com/chaosiq/chaosiq-agent/actions)
[![Docker Pulls](https://img.shields.io/docker/pulls/chaosiq/agent)](https://hub.docker.com/r/chaosiq/agent)

## Overview

This repository contains the agent that listens for Chaos Toolkit experiments
to run, from the ChaosIQ console, dispatched to the [Kubernetes operator][k8s-crd].

[k8s-crd]: https://github.com/chaostoolkit-incubator/kubernetes-crd

## Pre-requisite

Prior to the installation, you need to declare the agent on [ChaosIQ][console]:
- log into [ChaosIQ][console],
- go to the *Agents* page,
- add a new agent,
- reveal its token from the agents list and copy it.

The Agent token is necessary for the installation steps described below.

[console]: https://console.chaosiq.io/

## How to deploy?

The agent is intended to be deployed within your Kubernetes cluster alongside
the [Kubernetes operator][k8s-crd].

We suggest you use [Kustomize][kustomize] to generate the manifest to apply.

[kustomize]: https://github.com/kubernetes-sigs/kustomize

First, create the configuration file using the sample:

```
$ cp deploy/k8s/kustomize/overlays/generic/data/.env.sample deploy/k8s/kustomize/overlays/generic/data/.env
```

Then, edit the `.env` file and paste your agent token into the
`AGENT_ACCESS_TOKEN` field
```
AGENT_ACCESS_TOKEN=<paste your token here>
```

Finally, simply run the following command:

```
$ kustomize build deploy/k8s/kustomize/overlays/generic | kubectl apply -f -
```

If everything goes to plan, you should have the agent running:

```
$ kubectl -n chaosiq-agent logs -l app=chaosiq-agent
```


### Use a custom Chaos Toolkit docker image

The default docker image used to run the experiment can be customized at
installation.

To do so, simply edit the configuration file
`deploy/k8s/kustomize/overlays/generic/data/.env` and change the value of the
`CTK_DOCKER_IMAGE` field.

## Contribute

### Runtime Requirements

To run this project, you need the following:

* [Python 3.8](https://www.python.org/) or greater

### Development Requirements

To develop on this project, you must have the following dependencies setup:

* [Python 3.8](https://www.python.org/) or greater
* A virtual environment with `pip`

Once that virtual environment is created, install the dependencies into it:

```
$ pip install -U -r requirements.txt -r requirements-dev.txt
```

Then deploy the project source in "development mode" into the virtual
environment:

```
$ pip install -e .
```

### Setup a virtual environment

You may create a local virtual environment as follows:

```
$ cd chaosiq-agent
$ python3 -m venv .venv
$ source .venv/bin/activate
```

Run the last command everytime you create a new shell so you are in the right
Python environment.

### Run the service locally

To run the application locally, simply run the following commands:

```
$ source .venv/bin/activate
$ chaosiq-agent run --config=config/.env.sample
```

### Run the tests

To run the tests:

```
$ source .venv/bin/activate
$ pytest
```

The tests expects 100% coverage to succeed. Please change the setup.cfg file
to remove/reduce that constraint.

### Run the linter

To run the tests:

```
$ source .venv/bin/activate
$ pylama chaosiqagent
```

The linter will check the syntax as well as the types through mypy.
