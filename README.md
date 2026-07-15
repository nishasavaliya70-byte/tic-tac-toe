# Tic-Tac-Toe

A Tic-Tac-Toe game built with Python and [pygame](https://www.pygame.org/). Play as **X** against a computer opponent (**O**) powered by the minimax algorithm.

## Features

- Welcome screen where you choose who goes first
- Computer opponent using minimax, with adjustable skill so it doesn't always play perfectly
- Animated mark placement
- Scoreboard tracking wins for X, O, and draws
- Winning line highlight
- Sound effects (generated at runtime, no audio files needed)

## Requirements

- Python 3
- [pygame](https://pypi.org/project/pygame/)
- [numpy](https://pypi.org/project/numpy/)

Install dependencies:

```
pip install pygame numpy
```

## Run

```
python tic.py
```

## Controls

- **Click** a cell to place your mark
- **R** — restart the current match (after a win/draw)
- **M** — return to the welcome screen
- **Esc** — quit

## How it works

The computer's move is chosen with a minimax search over the full game tree, so on its best days it never loses. A `COMPUTER_SKILL` setting (in `tic.py`) controls how often it plays that optimal move versus a random one, making it possible to beat.
