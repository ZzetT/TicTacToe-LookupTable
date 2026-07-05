import sys

# A small, deliberately flawed lookup table for O's moves (player 2).
# 'X' is player 1.
# Keys are board states (tuples) when it's O's turn.
# Values are the index (0-8) where O should move.

import json

def load_minimized_rules():
    with open("minimized_rules.json", "r") as f:
        data = json.load(f)
    return {tuple(k): v for k, v in data.items()}

MINIMIZED_TABLE = load_minimized_rules()




def print_board(board):
    """Prints the 3x3 Tic-Tac-Toe board."""
    print("\nBoard:")
    for i in range(0, 9, 3):
        print(f" {board[i]} | {board[i+1]} | {board[i+2]} ")
        if i < 6:
            print("---|---|---")

def check_win(board, player):
    """Checks if the given player has won."""
    win_conditions = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8), # Rows
        (0, 3, 6), (1, 4, 7), (2, 5, 8), # Columns
        (0, 4, 8), (2, 4, 6)             # Diagonals
    ]
    for wc in win_conditions:
        if all(board[i] == player for i in wc):
            return True
    return False

def check_draw(board):
    """Checks if the game is a draw (board full, no winner)."""
    return ' ' not in board

def get_possible_moves(board):
    """Returns a list of indices for empty spots."""
    return [i for i, spot in enumerate(board) if spot == ' ']

def make_move(board, move, player):
    """Returns a new board tuple with the move applied."""
    board_list = list(board)
    if board_list[move] == ' ':
        board_list[move] = player
        return tuple(board_list)
    else:
        raise ValueError("Invalid move: Spot already taken")

def find_matching_move(board, minimized_table):
    matches = []

    # 1. Collect all patterns in the table that match the current board
    for pattern, move in minimized_table.items():
        match = True
        for p_char, b_char in zip(pattern, board):
            if p_char == '?':
                continue
            elif p_char == '!' and b_char != 'O':
                continue
            elif p_char == '*' and b_char != 'X':
                continue
            elif p_char == '+' and b_char != ' ':
                continue
            elif p_char == b_char:
                continue
            else:
                match = False
                break 
        
        if match:
            matches.append((pattern, move))
            
    if not matches:
        return None

    # 2. Check if the matched patterns disagree on which move to make
    first_move = matches[0][1]
    for pattern, move in matches:
        if move != first_move:
            print("\n" + "!"*40)
            print("!!! ERROR: AMBIGUOUS MOVE IN LOOKUP TABLE !!!")
            print(f"Board state matches multiple rules with DIFFERENT moves.")
            print_board(board)
            print(f"Board tuple: {board}")
            print("\nConflicting Rules:")
            for p, m in matches:
                print(f"  Pattern: {p} -> Move: {m}")
            print("!"*40)
            raise Exception("Conflicting moves found for the same board state")

    # 3. If all matches agree (or there is only one), return the move
    return first_move

def test_moves(board, player, minimized_table):
    """
    Recursively tests all game paths using the minimized table.
    """
    if player == 'X':
        # --- X's Turn: Try all possible moves ---
        for x_move in get_possible_moves(board):
            next_board = make_move(board, x_move, 'X')
            
            if check_win(next_board, 'X'):
                continue 
            if check_draw(next_board):
                continue 
                
            test_moves(next_board, 'O', minimized_table)

    elif player == 'O':
        # --- O's Turn: Use the minimized lookup table ---
        
        o_move = find_matching_move(board, minimized_table)
        
        # ERROR CHECK 2: Is a reply available?
        if o_move is None:
            print("\n" + "="*40)
            print("!!! ERROR: NO REPLY FOUND IN MINIMIZED TABLE !!!")
            print(f"Missing rule for board state:")
            print_board(board)
            print(f"Board tuple: {board}")
            print("="*40)
            raise Exception("Missing lookup reply")
            
        # Validate the move from the lookup table
        if board[o_move] != ' ':
            print("\n" + "="*40)
            print("!!! ERROR: INVALID MOVE IN MINIMIZED TABLE !!!")
            print(f"Lookup table suggested an illegal move (spot taken).")
            print_board(board)
            print(f"Suggested move: {o_move}")
            print("="*40)
            raise Exception("Invalid lookup move")

        next_board = make_move(board, o_move, 'O')
        
        if check_win(next_board, 'O'):
            return 
        if check_draw(next_board):
            return 
            
        # --- ERROR CHECK 1: Can 'X' win *after* O's move? ---
        for future_x_move in get_possible_moves(next_board):
            board_after_future_x = make_move(next_board, future_x_move, 'X')
            
            if check_win(board_after_future_x, 'X'):
                print("\n" + "="*40)
                print("!!! ERROR: MINIMIZED TABLE ALLOWS X TO WIN !!!")
                print("O's generalized move resulted in a blunder.")
                print("\nBoard state before O's move:")
                print_board(board)
                print(f"Board tuple: {board}")
                print(f"\nO's (bad) move: {o_move}")
                print("\nBoard state after O's move:")
                print_board(next_board)
                print(f"Board tuple: {next_board}")
                print(f"\nX's winning reply: {future_x_move}")
                print("\nResulting winning board for X:")
                print_board(board_after_future_x)
                print("="*40)
                raise Exception("Minimized table led to a loss")

        test_moves(next_board, 'X', minimized_table)

if __name__ == "__main__":

    print("Starting Minimized Tic-Tac-Toe table test...")
    initial_board = (' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ')
    
    try:
        # Ensure that every pattern explicitly requires an empty space at its move index
        for pattern, move in MINIMIZED_TABLE.items():
            if pattern[move] != ' ':
                raise ValueError(f"Pattern {pattern} does not have ' ' at move position {move}.")
                
        test_moves(initial_board, 'X', MINIMIZED_TABLE)
        print("\n" + "="*40)
        print("--- TEST COMPLETE: No errors found. ---")
        print("The minimized lookup table is consistent and perfect.")
        print("="*40)
        
    except Exception as e:
        print(f"\n--- TEST HALTED due to error: {e} ---")
        sys.exit(1)