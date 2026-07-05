import sys
from typing import Tuple, List, Set, Dict, Optional
import json

PLAYER_X = 'X'
PLAYER_O = 'O'
EMPTY = ' '

Board = Tuple[str, ...]

def get_initial_board() -> Board:
    """Returns an empty 9-spot board."""
    return (EMPTY,) * 9

def print_board(board: Board) -> None:
    """Prints a 3x3 representation of the board."""
    print("\n---")
    for i in range(0, 9, 3):
        print(f" {board[i]} | {board[i+1]} | {board[i+2]} ")
        if i < 6:
            print("---+---+---")
    print("---")

def check_win(board: Board) -> Optional[str]:
    """Checks if a player ('X' or 'O') has won. Returns winner or None."""
    win_conditions = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),  # Rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8),  # Columns
        (0, 4, 8), (2, 4, 6)             # Diagonals
    ]
    for a, b, c in win_conditions:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]  # Return the winner ('X' or 'O')
    return None

def is_draw(board: Board) -> bool:
    """Checks if the game is a draw (no winner and no empty spots)."""
    return check_win(board) is None and EMPTY not in board

def get_available_moves(board: Board) -> List[int]:
    """Returns a list of indices (0-8) that are empty."""
    return [i for i, spot in enumerate(board) if spot == EMPTY]

def make_move(board: Board, move: int, player: str) -> Board:
    """Returns a new board state (tuple) after making a move."""
    board_list = list(board)
    board_list[move] = player
    return tuple(board_list)

# --- Minimax Algorithm (For the "Perfect" 'O' Player) ---

# Memoization cache for minimax scores
# Key: (board_tuple, is_maximizing_player)
# Value: score
minimax_memo: Dict[Tuple[Board, bool], int] = {}

def minimax(board: Board, is_maximizing_player: bool) -> int:
    """
    Calculates the optimal score for a given board state.
    'O' is the maximizer (score 1 for win, 0 for draw, -1 for loss).
    'X' is the minimizer.
    """
    state_key = (board, is_maximizing_player)
    if state_key in minimax_memo:
        return minimax_memo[state_key]

    # --- Base Cases (Game Over) ---
    winner = check_win(board)
    if winner == PLAYER_O:
        return 1  # 'O' (Computer) wins
    if winner == PLAYER_X:
        return -1 # 'X' (Human) wins
    if is_draw(board):
        return 0  # Draw

    # --- Recursive Cases ---
    
    if is_maximizing_player:  # 'O' (Computer's) turn
        best_score = -sys.maxsize
        for move in get_available_moves(board):
            new_board = make_move(board, move, PLAYER_O)
            # The next turn belongs to the minimizer ('X')
            score = minimax(new_board, False)
            best_score = max(best_score, score)
        minimax_memo[state_key] = best_score
        return best_score
        
    else:  # 'X' (Human's) turn
        best_score = sys.maxsize
        for move in get_available_moves(board):
            new_board = make_move(board, move, PLAYER_X)
            # The next turn belongs to the maximizer ('O')
            score = minimax(new_board, True)
            best_score = min(best_score, score)
        minimax_memo[state_key] = best_score
        return best_score

# Memoization cache for subtree sizes
# Key: (board_tuple, current_player)
# Value: size (int)
subtree_size_memo: Dict[Tuple[Board, str], int] = {}

def get_subtree_size(current_board: Board, current_player: str) -> int:
    """
    Calculates the *absolute* size of the game tree from this state,
    following the asymmetric rules (X-all, O-best-with-tiebreak).
    Uses its own memoization and does NOT affect all_states.
    """
    state_key = (current_board, current_player)
    if state_key in subtree_size_memo:
        return subtree_size_memo[state_key]

    # Base case: Game over
    if check_win(current_board) or is_draw(current_board):
        subtree_size_memo[state_key] = 1  # This state counts as 1
        return 1

    total_size = 1  # Count the current state

    # --- Recursive Step: Player 'X' (Human) ---
    if current_player == PLAYER_X:
        for move in get_available_moves(current_board):
            new_board = make_move(current_board, move, PLAYER_X)
            # Size is 1 (current) + sum of all child sub-trees
            total_size += get_subtree_size(new_board, PLAYER_O)
    
    # --- Recursive Step: Player 'O' (Computer) ---
    elif current_player == PLAYER_O:
        available_moves = get_available_moves(current_board)
        
        if not available_moves:
            subtree_size_memo[state_key] = total_size  # 1
            return total_size

        # 1. Find best minimax score
        best_score = -sys.maxsize
        scores_by_move: Dict[int, int] = {}
        for move in available_moves:
            new_board = make_move(current_board, move, PLAYER_O)
            score = minimax(new_board, False)
            scores_by_move[move] = score
            best_score = max(best_score, score)

        # 2. Filter for moves with that score
        best_moves: List[int] = [m for m, s in scores_by_move.items() if s == best_score]

        chosen_move = -1
        
        if len(best_moves) == 1:
            chosen_move = best_moves[0]
        else:
            # 3. Tie-breaker: Find smallest sub-tree by *recursively calling this function*
            min_child_subtree_size = sys.maxsize
            chosen_move = best_moves[0]  # Default to first
            
            for move in best_moves:
                new_board = make_move(current_board, move, PLAYER_O)
                # Recursively call get_subtree_size to find the size of the *next* state
                child_subtree_size = get_subtree_size(new_board, PLAYER_X)
                
                if child_subtree_size < min_child_subtree_size:
                    min_child_subtree_size = child_subtree_size
                    chosen_move = move

        # 4. Add the size of *only* that chosen sub-tree.
        if chosen_move != -1:
            best_board = make_move(current_board, chosen_move, PLAYER_O)
            total_size += get_subtree_size(best_board, PLAYER_X)

    # Memoize and return the final calculated size
    subtree_size_memo[state_key] = total_size
    return total_size

def find_best_move_for_state(board: Board) -> Optional[int]:
    """
    Finds the single best move for the current player of a given board state.
    - For 'O' (computer): Uses minimax score, then smallest sub-tree tiebreak.
    - For 'X' (human): Uses pure minimax score (no sub-tree tiebreak specified).
    """
    # 1. Check for game over
    if check_win(board) or is_draw(board):
        return None

    # 2. Determine current player
    x_count = board.count(PLAYER_X)
    o_count = board.count(PLAYER_O)
    current_player = PLAYER_X if x_count == o_count else PLAYER_O

    available_moves = get_available_moves(board)
    if not available_moves:
        return None # Should be caught by is_draw, but as a safeguard

    # 3. 'O' (Computer's) turn
    if current_player == PLAYER_O:
        best_score = -sys.maxsize
        scores_by_move: Dict[int, int] = {}
        for move in available_moves:
            new_board = make_move(board, move, PLAYER_O)
            # Next player is 'X' (minimizer)
            score = minimax(new_board, False) 
            scores_by_move[move] = score
            best_score = max(best_score, score)

        # Filter for moves that achieve the best score
        best_moves: List[int] = [m for m, s in scores_by_move.items() if s == best_score]

        if len(best_moves) == 1:
            return best_moves[0]
        
        # Tie-breaker: Find smallest sub-tree
        min_subtree_size = sys.maxsize
        chosen_move = best_moves[0]
        for move in best_moves:
            new_board = make_move(board, move, PLAYER_O)
            # The size of the *resulting* tree is needed, where it is 'X's turn
            subtree_size = get_subtree_size(new_board, PLAYER_X) 
            if subtree_size < min_subtree_size:
                min_subtree_size = subtree_size
                chosen_move = move
        return chosen_move

    # 4. 'X' (Human's) turn
    else: # current_player == PLAYER_X
        # Find the pure minimax move for 'X' (minimizer)
        best_score = sys.maxsize
        chosen_move = available_moves[0] # Default to first move
        
        for move in available_moves:
            new_board = make_move(board, move, PLAYER_X)
            # Next player is 'O' (maximizer)
            score = minimax(new_board, True)
            if score < best_score:
                best_score = score
                chosen_move = move
        # No tie-breaker specified for 'X', return the first one found
        return chosen_move

def collect_reachable_states(
    current_board: Board,
    current_player: str,
    all_states: Set[Board]
) -> None:
    """
    Recursively explores the game tree based on the asymmetric rules.
    - 'X' explores all possible moves.
    - 'O' explores only the single best move (using score, then sub-tree size).
    
    Populates the `all_states` set with all visited board tuples.
    """
    
    # 1. Add the current state to the set.
    #    If seen before, it is already explored.
    if current_board in all_states:
        return
    all_states.add(current_board)

    # 2. Check for game-over conditions (base case)
    if check_win(current_board) or is_draw(current_board):
        return

    # 3. Recursive Step: Player 'X' (Human)
    if current_player == PLAYER_X:
        # 'X' may choose *any* move. All branches must be explored.
        for move in get_available_moves(current_board):
            new_board = make_move(current_board, move, PLAYER_X)
            collect_reachable_states(new_board, PLAYER_O, all_states)
            
    # 4. Recursive Step: Player 'O' (Computer)
    elif current_player == PLAYER_O:
        # 'O' *always* plays the best move.
        
        available_moves = get_available_moves(current_board)
        # If no moves, the draw/win check would have caught it.
        if not available_moves:
            return

        # 1. Find best minimax score
        best_score = -sys.maxsize
        scores_by_move: Dict[int, int] = {}
        for move in available_moves:
            new_board = make_move(current_board, move, PLAYER_O)
            score = minimax(new_board, False)
            scores_by_move[move] = score
            best_score = max(best_score, score)

        # 2. Filter for moves with that score
        best_moves: List[int] = [m for m, s in scores_by_move.items() if s == best_score]

        chosen_move = -1
        
        if len(best_moves) == 1:
            chosen_move = best_moves[0]
        else:
            # 3. Tie-breaker: Find smallest sub-tree
            min_subtree_size = sys.maxsize
            chosen_move = best_moves[0] # Default to first
            
            for move in best_moves:
                new_board = make_move(current_board, move, PLAYER_O)
                # Get the pre-calculated size
                subtree_size = get_subtree_size(new_board, PLAYER_X)
                
                if subtree_size < min_subtree_size:
                    min_subtree_size = subtree_size
                    chosen_move = move
                        
        # 4. Found the *single* best move (by score, then by size).
        #    Explore only that path.
        if chosen_move != -1:
            best_board = make_move(current_board, chosen_move, PLAYER_O)
            collect_reachable_states(best_board, PLAYER_X, all_states)

if __name__ == "__main__":
    print("Calculating all reachable Tic-Tac-Toe states...")
    print("Rules:")
    print(" 1. Player 'X' (Human) starts and can play any valid move.")
    print(" 2. Player 'O' (Computer) *always* plays the single best optimal move.")
    print(" 3. If 'O' has multiple moves with the same score, it picks the one")
    print("    leading to the *smallest* game sub-tree.")
    print("\nThis may take a bit longer now...\n")
    
    # Clear the memoization caches for a fresh run
    minimax_memo.clear()
    subtree_size_memo.clear()
    
    # This set will store all unique board tuples
    reachable_states: Set[Board] = set()
    
    initial_board = get_initial_board()
    
    # This is the most expensive part, done once.
    print("Pre-calculating all game tree sub-tree sizes... ")
    get_subtree_size(initial_board, PLAYER_X)
    print("Sub-tree calculation complete.")

    print("Collecting the final set of reachable states...")
    collect_reachable_states(initial_board, PLAYER_X, reachable_states)
    
    print("\n--- Results ---")
    print(f"Total unique reachable states found (all turns): {len(reachable_states)}")
    
    print("\n--- 'O's Turn: Python Lookup Table ---")
    
    # Sort the states for a consistent output
    # Sorting by sum of 'X'/'O' (i.e., move count) is a good proxy for game progression
    sorted_states = sorted(
        reachable_states, 
        key=lambda b: b.count(PLAYER_X) + b.count(PLAYER_O)
    )

    o_turn_lookup: Dict[Board, int] = {}
    
    for state in sorted_states:
        # Check for game over
        if check_win(state) or is_draw(state):
            continue
            
        # Check if it's 'O's turn (X has made more moves or equal, but X starts)
        # O's turn means X count > O count
        is_o_turn = state.count(PLAYER_X) > state.count(PLAYER_O)

        if is_o_turn:
            best_move = find_best_move_for_state(state)
            
            if best_move is not None:
                o_turn_lookup[state] = best_move
        
    # Print the dictionary in a Python-readable format
    print("# Optimal move lookup table for 'O'")
    print("# Key: Board tuple, Value: Best move (index 0-8)")
    print("O_MOVE_LOOKUP = {")
    for state, move in o_turn_lookup.items():
        # Pad the state string for alignment (approx 60 chars)
        print(f"    {state!s:<65}: {move},")
    print("}")
    
    # Save raw moves to JSON
    json_lookup = {"".join(state): move for state, move in o_turn_lookup.items()}
    with open("raw_moves.json", "w") as f:
        json.dump(json_lookup, f, indent=4)
    print("Saved raw moves to raw_moves.json")
        
    print(f"\nTotal states where 'O' has a move: {len(o_turn_lookup)}")

    # --- Optional: Show some examples ---
    print("\n--- Example States (from full list) ---")