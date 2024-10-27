# Pycider

This code is a Python implementation of deciders based on the F# code from [Jérémie Chassaing](https://github.com/thinkbeforecoding/) located here [dddeu-2023-deciders](https://github.com/thinkbeforecoding/dddeu-2023-deciders). There was additionally a talk on this, to be found [here](https://www.youtube.com/watch?v=72TOhMpEVlA).

## Installation

You can use `pip install pycider` or `poetry add pycider` to install this project from [PyPI](https://pypi.org/project/pycider/).

## Usage

You can create `Process` or a `Decider`. A simple example of this can be found under the [test composition page](./tests/test_compositions.py). 

## Decider 

`Decider` is a simple state machine that seperate state changes and actions. Actions are `Command`s which when executed return `Event`s, representing the results from executing a `Command`. You can use `Event`'s to deterministically update the `State` allowing replayability and easy serialization by only saving `Event`'s. 

* `Command`s are turned into `Event`'s through `decide()` calls.
* `Event`'s deterministically update the `State` through `evolve()` calls.

## Process

TODO
