# Tetris AI
 
A heuristic AI that plays a bomb-and-discard variant of Tetris, together with a genetic-algorithm optimizer that automatically tunes the AI's evaluation weights. Built for UCL ENGF0034.
 
The game supports manual play across three front ends — pygame, tkinter, and a terminal/curses interface — and can also be played remotely over a simple text-based wire protocol.
 
## The AI — `player.py`
 
`TetrisPlayerAI` picks each move by simulating every rotation and column for the current piece, scoring the resulting board, and choosing the best placement. The evaluation is a weighted sum of four heuristics:
 
- **Gaps** — empty cells trapped beneath placed blocks
- **Max height** — height of the tallest column
- **Almost-complete lines** — rows one cell short of clearing
- **Bumpiness** — total height difference between adjacent columns
It also plays the variant's two special mechanics:
 
- **Bombs** — used when the stack gets dangerously high or accumulates too many gaps, targeting the worst column.
- **Discards** — used to skip a bad piece when placing it would add gaps without clearing lines, holding the final discard back for genuinely dangerous boards.
Once the board is roughly 60%+ full, the AI switches to a more aggressive scoring mode that prioritises clearing lines over tidiness.
 
## The optimizer — `optimizer.py`
 
A genetic algorithm that tunes the AI's four weights:
 
- Evaluates a population of weight sets over many seeded games each
- Selects for **high median score and low variance** — fitness penalises inconsistency, not just low scores
- Evolves across generations using elitism, tournament selection, weighted-average crossover, and bounded mutation
- Writes the best weights it finds back into `player.py`
## Requirements
 
- Python 3
- `pygame` for `visual-pygame.py` — `pip install pygame`
- `tkinter` for `visual.py` — bundled with most Python installs
- A Unix terminal with `curses` for `cmdline.py`
- The included `Segment7-4Gml.otf` font (used for the pygame score display)
## Running it
 
Watch the AI play (pygame front end):
```bash
python visual-pygame.py
```
 
Play manually instead:
```bash
python visual-pygame.py --manual
```
 
Other front ends (add `--manual` to play yourself):
```bash
python visual.py      # tkinter window
python cmdline.py     # terminal / curses
```
 
Tune the AI's weights with the genetic optimizer:
```bash
python optimizer.py
```
 
## Controls (manual mode)
 
| Key | Action |
|-----|--------|
| ← / → | Move left / right |
| ↓ | Move down |
| ↑ or x | Rotate clockwise |
| z | Rotate anticlockwise |
| Space | Hard drop |
| b | Use bomb |
| d | Discard piece |
| Esc / q | Quit |
 
## Game parameters
 
Defined in `constants.py`: a 10×24 board, a fixed RNG seed for reproducible games, and a 400-block limit per game.
