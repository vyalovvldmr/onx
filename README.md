# Noughts & Crosses (Tic Tac Toe)

[![RunTests](https://github.com/vyalovvldmr/onx/actions/workflows/run_tests.yml/badge.svg)](https://github.com/vyalovvldmr/onx/actions/workflows/run_tests.yml)

Client-server Noughts & Crosses (Tic Tac Toe) terminal based, online game through websockets.

## Requires

Python 3.10

## Install

```
$ pip install onx
```

## Play Game

```
$ onx
```

![TUI screenshot 1](https://github.com/vyalovvldmr/onx/blob/master/static/screen1.png?raw=true)

Command line option `-g` or `--grid-size` changes grid size.
Option `-w` or `--wining-length` changes winning sequence length.
Option `-h` or `--help` prints help.

```
$ onx -g14 -w3
```

![TUI screenshot 1](https://github.com/vyalovvldmr/onx/blob/master/static/screen2.png?raw=true)

## Run Server and Client Locally

Set up env variables.

```
$ export LOCALHOST="0.0.0.0"
$ export PORT=8888
```

Run server.

```
$ onx -d
```

Run client.

```
$ onx
```

## Run Tests

```
$ git clone git@github.com:vyalow/onx.git
$ cd onx
$ pip install -r requirements.txt -r requirements-dev.txt
$ pytest --cov
```

## TODO

- [x] Bump up Python version from 3.5 to 3.10
- [x] Fix tests stability after bumping aiohttp from 1.3 to 3.8
- [x] Set up code linting
- [x] Set up mypy
- [x] Better client
- [x] Add to PyPI
- [x] Heroku deployment
- [x] Expand play board
- [ ] Fix aiohttp deprecations
- [ ] Migrate from aiohttp to starlette or gRPC or even Blockchain
- [ ] Add gameplay with a computer
