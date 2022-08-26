# Noughts & Crosses

[![RunTests](https://github.com/vyalovvldmr/ttt/actions/workflows/run_tests.yml/badge.svg)](https://github.com/vyalovvldmr/ttt/actions/workflows/run_tests.yml)

Client-server Noughts & Crosses (Tic Tac Toe) terminal based, multiplayer game through websockets.

### Requires

Python 3.10

### Install

```
$ git clone git@github.com:vyalow/ttt.git
$ cd ttt
$ pip install -r requirements.txt
```

### Run game

```
$ python ttt.py
```

![TUI screenshot](screen.png)

### Run server

```
$ python ttt.py -d
```

### Run tests

```
$ pip install -r requirements-dev.txt
$ pytest --cov
=========================== test session starts ================================
platform darwin -- Python 3.10.5, pytest-7.1.2, pluggy-1.0.0
rootdir: ttt
plugins: cov-3.0.0
collected 13 items                    

tests/test_game.py ....         [ 30%]
tests/test_validation.py .....  [ 69%]
tests/test_ws_server.py ....    [100%]

---------- coverage: platform darwin, python 3.10.5-final-0 ----------
Name              Stmts   Miss  Cover
-------------------------------------
ttt/__init__.py       0      0   100%
ttt/api.py           22      0   100%
ttt/app.py            7      0   100%
ttt/errors.py         2      0   100%
ttt/game.py          90      1    99%
ttt/handler.py       43      1    98%
ttt/settings.py       6      0   100%
-------------------------------------
TOTAL               170      2    99%


============================ 13 passed in 0.29s ================================
```

### TODO

- [x] Bump up Python version from 3.5 to 3.10
- [x] Fix tests stability after bumping aiohttp from 1.3 to 3.8
- [x] Set up code linting
- [x] Set up mypy
- [ ] Fix aiohttp deprecations
- [x] Better client
- [ ] Add to PyPI
- [ ] Heroku deployment
- [ ] Migrate from aiohttp to starlette or migrate from websockets to gRPC
- [ ] Expand play board
- [ ] Add gameplay with a computer
