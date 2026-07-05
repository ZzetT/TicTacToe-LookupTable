# TicTacToe LookupTable (for 'O')

This repository consists of Python scripts to calculate, compress, and verify the optimal lookup table for the 2nd player ('O') of Tic Tac Toe, which plays a perfect game (i.e., never loses). Only reachable states are considered (i.e., the lookup table is only applicable if you played the game according to the lookup table; you cannot use it to find the best move for an arbitrary board state).

The pipeline is split into three automated steps:

1. **`01_generate_moves.py`**: The minimal game tree of Tic Tac Toe is calculated by searching the reachable game space and applying a subtree-size tiebreaker when evaluating equivalently optimal moves. This results in a raw lookup table (saved as `raw_moves.json`) which maps the board state—consisting of 'X', 'O', or ' ' (blank)—to an optimal reply move for 'O'.
2. **`02_minimize_rules.py`**: This script compresses the raw lookup table into a minimal set of generalized rules using Integer Linear Programming (ILP) with PuLP. To maximize compression, it introduces the following wildcards:
   - `?` : Matches any state ('X', 'O', or ' ')
   - `!` : Matches not 'O' ('X' or ' ')
   - `*` : Matches not 'X' ('O' or ' ')
   
   *(Note: There is no wildcard representing "X or O" because it was not possible to generate a physical card for it in the machine.)*
   
   It exports the final compressed table to `minimized_rules.json`.
3. **`03_verify_rules.py`**: A lightweight verification script that runs all possible reachable game paths against the minimized rules to ensure the compressed logic is 100% accurate and conflict-free.

The output of this pipeline is used in my [Unbeatable Tic Tac Toe Machine "XXO-Master"](https://www.printables.com/model/1745561-unbeatable-tic-tac-toe-machine-xxo-master). More information can also be watched in my [explanation video](https://youtu.be/0ECLzEu6Fs4?si=Co0qcNGiWl411_LQ).

## Installation & Usage

To run the pipeline yourself, you'll need Python 3 installed. It's recommended to use a virtual environment.

1. **Install Dependencies**: The minimization step requires the `pulp` library for Integer Linear Programming.
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Pipeline**: Execute the scripts in order:
   ```bash
   python 01_generate_moves.py
   python 02_minimize_rules.py
   python 03_verify_rules.py
   ```
