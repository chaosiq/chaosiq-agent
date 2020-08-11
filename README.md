# Welcome to the chaosiq-agent project

## Overview

This provides is the ChaosIQ agent which allows to automatically schedule
Chaos Toolkit experiments as jobs in your environment.

## Requirements

### Runtime Requirements

To run this project, you need the following:

* [Python 3.8](https://www.python.org/) or greater

### Development Requirements

To develop on this project, you must have the following dependencies setup:

* [Python 3.8](https://www.python.org/) or greater
* A virtual environment with `pip`

### Setup a virtual environment

You may create a local virtual environment as follows:

```
$ cd chaosiq-agent
$ python3 -m venv .venv
$ source .venv/bin/activate
```

Run the last command everytime you create a new shell so you are in the right
Python environment.

## Run the service locally

To run the application locally, simply run the following commands:

```
$ source .venv/bin/activate
$ chaosiq-agent run --config=.config/.env.sample
```

## Run the tests

To run the tests:

```
$ source .venv/bin/activate
$ pytest
```

The tests expects 100% coverage to succeed. Please change the setup.cfg file
to remove/reduce that constraint.

## Run the linter

To run the tests:

```
$ source .venv/bin/activate
$ pylama chaosiqagent
```

The linter will check the syntax as well as the types through mypy.
