# Noughts & Crosses
Test for a job application.

Client-server Noughts & Crosses game through websockets.

### Requires

Python >= 3.5

### Installation

```
$ git clone git@github.com:vyalow/noughts_and_crosses.git
$ cd noughts_and_crosses
$ pip install -r requirements.txt
```

### Run server

`python server.py`

### Run client

`python client.py`

### Run tests

```
$ nosetests --with-coverage --cover-package=noughts_and_crosses
.........
Name                                Stmts   Miss  Cover
-------------------------------------------------------
noughts_and_crosses.py                  0      0   100%
noughts_and_crosses/app.py              7      0   100%
noughts_and_crosses/errors.py           2      0   100%
noughts_and_crosses/game.py            53      0   100%
noughts_and_crosses/game_pool.py       25      1    96%
noughts_and_crosses/ws_handler.py      40      1    98%
noughts_and_crosses/ws_utils.py         8      0   100%
-------------------------------------------------------
TOTAL                                 135      2    99%
----------------------------------------------------------------------
Ran 9 tests in 0.288s

OK
```
