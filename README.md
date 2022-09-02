# Noughts & Crosses (Tic Tac Toe)

[![RunTests](https://github.com/vyalovvldmr/onx/actions/workflows/run_tests.yml/badge.svg)](https://github.com/vyalovvldmr/onx/actions/workflows/run_tests.yml)

Noughts & Crosses (Tic Tac Toe) terminal based, client-server online game with your partner through websockets.

## Requires

Python 3.10

## Install

```
$ pip install onx
```

or

```
$ poetry shell
$ poetry add onx
```

## Play Game

For running your game board just type in a terminal:

```
$ onx
```

You will see a game board in a waiting for your partner state.

Then ask your partner to run the same cli command with **exactly** the same cli options.
You will be matched to your partner by cli options (size and winning sequence length) on a server side.

If you are running a game with a public server than I'll suggest you to make a shorter delay between running your game board and your partners board. Just for reducing the probability to be matched with somebody else.


![TUI screenshot 1](https://github.com/vyalovvldmr/onx/blob/master/static/screen1.png?raw=true)

There are command line options for changing game board settings.
`-g` or `--grid-size` changes grid size.
`-w` or `--wining-length` changes winning sequence length.
`-h` or `--help` prints help.

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
$ poetry shell
$ poetry install --no-root
$ pytest --cov
```

## Known Limitations

- **onx** is currently based on [textual](https://github.com/Textualize/textual) TUI framework which is awesome
  but is at an extremely early development stage. As a result you may be faced with some rendering problem like [711](https://github.com/Textualize/textual/issues/711), [710](https://github.com/Textualize/textual/issues/710).
  I'll suggest you to run a game board in a fullscreen mode for now.
- Public server is currently running on a free Heroku app. It means that a good enough SLA is not expected.

## Release

```
make release version=[patch | minor | major]
```
