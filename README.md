# TicTacToe LookupTable (for 'O')

This repository consists of Python scripts to calculate, compress, and verify the optimal lookup table for the 2nd player ('O') of Tic Tac Toe, which plays a perfect game (i.e., never loses). Only reachable states are considered (i.e., the lookup table is only applicable if you played the game according to the lookup table; you cannot use it to find the best move for an arbitrary board state).

*(Note: This repository does not contain any code to generate the STLs of the cards or the machine. I might upload them at some point.)*
The pipeline is split into three automated steps:

1. **`01_generate_moves.py`**: The minimal game tree of Tic Tac Toe is calculated by searching the reachable game space and applying a subtree-size tiebreaker when evaluating equivalently optimal moves. This results in a raw lookup table (saved as `raw_moves.json`) which maps the board state—consisting of 'X', 'O', or ' ' (blank)—to an optimal reply move for 'O'.
2. **`02_minimize_rules.py`**: This script compresses the raw lookup table into a minimal set of generalized rules. It achieves this in two main phases:
   - **Pattern Generalization (BFS)**: For each unique target move, it groups all base states leading to that move and performs a Breadth-First Search. This incrementally generalizes the states using partial wildcards. A generalized pattern is considered valid only if it does not accidentally match any board state associated with a different target move.
   - **Exact Set Cover (Minimization)**: Using the `pulp` library, the problem is modeled as an Integer Linear Program (ILP). It solves an exact Set Cover problem to find the absolute minimum number of valid generalized patterns required to cover all original base states. It uses a slight penalty in the objective function to favor broader wildcards over narrower ones when breaking ties.
   
     *(Note: The Exact Set Cover problem is notoriously "NP-hard". Even though Tic Tac Toe is a relatively simple game, executing this minimization step can take a few minutes. If anyone has a better or more efficient solution for this exact minimization, feel free to let me know!)*
   
   To maximize compression, it introduces the following wildcards:
   - `?` : Matches any state ('X', 'O', or ' ')
   - `!` : Matches not 'O' ('X' or ' ')
   - `*` : Matches not 'X' ('O' or ' ')
   
   *(Note: There is no wildcard representing "X or O" because it was not possible to generate a physical card for it in the machine.)*
   
   It exports the final compressed table to `minimized_rules.json`.
3. **`03_verify_rules.py`**: A lightweight verification script that runs all possible reachable game paths against the minimized rules to ensure the compressed logic is 100% accurate and conflict-free.

The output of this pipeline is used in my 3D printing project [Unbeatable Tic Tac Toe Machine "XXO-Master"](https://www.printables.com/model/1745561-unbeatable-tic-tac-toe-machine-xxo-master). More information can also be watched in my [explanation video](https://youtu.be/0ECLzEu6Fs4?si=Co0qcNGiWl411_LQ).

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
