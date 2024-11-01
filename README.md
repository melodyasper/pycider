# Pycider

[![Documentation Status](https://readthedocs.org/projects/pycider/badge/?version=latest)](https://pycider.readthedocs.io/en/latest/?badge=latest)

[Documentation is here](http://pycider.readthedocs.io/). This code is a Python implementation of deciders based on the F# code from [Jérémie Chassaing](https://github.com/thinkbeforecoding/) located here [dddeu-2023-deciders](https://github.com/thinkbeforecoding/dddeu-2023-deciders). There was additionally a talk on this, to be found [here](https://www.youtube.com/watch?v=72TOhMpEVlA).

## Installation

You can use `pip install pycider` or `poetry add pycider` to install this project from [PyPI](https://pypi.org/project/pycider/).

## Usage

You can create `Process` or a `Decider`. A simple example of this can be found under the [test composition page](./tests/test_compositions.py). 

## Decider 

`Decider` is a simple state machine that seperates state changes and actions. `Command`s are actions which when executed return `Event`s representing the results from the actions. You can use `Event`'s to deterministically update the `State` allowing replayability and easy serialization by only saving `Event`'s. 

* `Command`s are turned into `Event`'s through `decide()` calls.
* `Event`'s deterministically update the `State` through `evolve()` calls.

## Process

`Process` is a simple state machine for managing a system. A system has several needs. The system given a `State` should be able to resume to the next `Command`, The system should be able to react to `Event` changes and return `Command`'s for dealing with those changes. Finally the system should be able to update the `State` deterministically given a `Event`. 

* `Event`'s are turned into `Command`s thrugh `react()` calls.
* Given a `State`, the system should be able to `resume()` to the appropriate `Command`.
* `Event`'s deterministically update the `State` through `evolve()` calls.

## Example: How do Process and Decider work together

A `Process` all about reacting to events and coordinating between `Decider`'s. 
