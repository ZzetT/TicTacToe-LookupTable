"""
Tic-Tac-Toe Lookup Table Reducer
================================

This script compresses a hardcoded Tic-Tac-Toe move lookup table into a minimal 
set of generalized rules using partial wildcards and Integer Linear Programming (ILP).

Wildcards used for generalization:
  '?' : Matches any state ('X', 'O', or ' ')
  '!' : Matches not 'O' ('X' or ' ')
  '*' : Matches not 'X' ('O' or ' ')

How it works:
1. Pattern Generalization (BFS):
   For each unique target move, the script groups all board states that result in that move. 
   It then performs a Breadth-First Search (BFS) to incrementally generalize these states 
   using the wildcards. A generalized pattern is kept valid only if it does not match 
   any state associated with a different move (an "invalid state").

2. Exact Set Cover (Minimization):
   Once all valid generalized patterns are found for a target move, the script uses 
   the `pulp` library to solve an exact Set Cover problem. It models the problem as 
   an Integer Linear Program (ILP) to find the absolute minimum number of generalized 
   patterns required to cover all the original base states for that move. The objective 
   function slightly penalizes narrower patterns to break ties in favor of broader wildcards.
"""
from collections import defaultdict
import pulp
import time

# The original lookup table provided
import json

def load_raw_moves():
    with open("raw_moves.json", "r") as f:
        data = json.load(f)
    return {tuple(k): v for k, v in data.items()}

O_MOVE_LOOKUP = load_raw_moves()

def pattern_matches(pattern, state):
    """
    Check if a pattern matches a specific board state.
    Optimized to bypass Python's zip() and generator overhead.
    """
    for i in range(9):
        p = pattern[i]
        if p == '?': continue
        
        s = state[i]
        if p == s: continue
        
        # Fast early-exit checks
        if p == '!':
            if s == 'O': return False
            continue
        if p == '*':
            if s == 'X': return False
            continue
            
        return False
    return True

def pattern_score(pattern):
    """
    Assign a mathematical weight to how broad a pattern is.
    Used to sort and prioritize patterns that cover the most scenarios.
    """
    score = 0
    score += pattern.count('?') * 3  # Covers 3 states
    score += pattern.count('!') * 2  # Covers 2 states
    score += pattern.count('*') * 2  # Covers 2 states
    return score

def reduce_lookup(lookup):
    """Compress the lookup table using partial wildcard generalizations."""
    states_by_move = defaultdict(list)
    for state, move in lookup.items():
        states_by_move[move].append(state)

    reduced_rules = []

    # Map for 1-step generalizations to avoid redundant paths in BFS
    GENERALIZATIONS = {
        'X': ['!'],
        'O': ['*'],
        ' ': ['!', '*'],
        '!': ['?'],
        '*': ['?'],
        '?': []
    }

    print(f"Analyzing {len(states_by_move)} unique moves. This may take a few seconds due to the expanded logic matrix...\n")
    start_time = time.time()

    for target_move, base_states in states_by_move.items():
        # States that this pattern MUST NOT match
        invalid_states = [s for s, m in lookup.items() if m != target_move]
        
        valid_patterns = set(base_states)
        visited = set(base_states)
        queue = list(base_states)

        print(f"Processing Move {target_move} (covering {len(base_states)} base states)...")
        explored_count = 0

        # 1. Exhaustive Generalization (BFS) with Partial Wildcards
        while queue:
            pat = queue.pop(0)
            explored_count += 1
            
            # Live progress tracker printed on the same line
            if explored_count % 2000 == 0:
                print(f"  -> Explored: {explored_count:,} | Queue: {len(queue):,} | Valid: {len(valid_patterns):,}", end='\r')

            for i in range(9):
                # Enforce that the target move position remains ' ' (empty)
                if i == target_move:
                    continue

                char = pat[i]
                for gen in GENERALIZATIONS.get(char, []):
                    new_pat = list(pat)
                    new_pat[i] = gen
                    new_pat = tuple(new_pat)

                    if new_pat not in visited:
                        visited.add(new_pat)
                        
                        # Verify the new generalized pattern doesn't conflict with invalid states
                        # (A raw for-loop is much faster than any() with a generator in Python)
                        conflict = False
                        for inv_s in invalid_states:
                            if pattern_matches(new_pat, inv_s):
                                conflict = True
                                break
                        
                        if not conflict:
                            valid_patterns.add(new_pat)
                            queue.append(new_pat)

        print(f"  -> Finished BFS. Found {len(valid_patterns):,} valid patterns. Running Set Cover...        ")

        # 2. Greedy Set Cover
# 2. Exact Set Cover using PuLP Integer Linear Programming
        print(f"  -> Running Exact Set Cover with PuLP...        ")
        
        prob = pulp.LpProblem(f"Minimize_Patterns_Move_{target_move}", pulp.LpMinimize)
        
        # Create a binary variable for every valid pattern (1 if used, 0 if not)
        pattern_vars = {p: pulp.LpVariable(f"pat_{i}", cat='Binary') for i, p in enumerate(valid_patterns)}
        
        # Objective: Minimize sum of chosen patterns (fractional penalty prefers broader wildcards)
        prob += pulp.lpSum([pattern_vars[p] - 0.0001 * pattern_score(p) * pattern_vars[p] for p in valid_patterns])
        
        # Constraints: Every base state MUST be covered
        for state in base_states:
            covering_patterns = [p for p in valid_patterns if pattern_matches(p, state)]
            prob += pulp.lpSum([pattern_vars[p] for p in covering_patterns]) >= 1
            
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        # Extract the chosen patterns
        for p in valid_patterns:
            if pattern_vars[p].varValue is not None and pattern_vars[p].varValue > 0.5:
                reduced_rules.append((p, target_move))

    # Sort rules simply for readable output
    reduced_rules.sort(key=lambda item: (item[1], -pattern_score(item[0])))
    
    elapsed = time.time() - start_time
    print(f"Compression completed in {elapsed:.2f} seconds.\n")
    return reduced_rules

if __name__ == "__main__":
    print(f"Original length: {len(O_MOVE_LOOKUP)} states")
    reduced_list = reduce_lookup(O_MOVE_LOOKUP)
    print(f"Reduced length: {len(reduced_list)} states\n")

    # Double-check that the compressed dictionary functions perfectly
    errors = 0
    for state, expected_move in O_MOVE_LOOKUP.items():
        matched = False
        for pat, move in reduced_list:
            if pattern_matches(pat, state):
                if move != expected_move:
                    print(f"ERROR: State {state} matched {pat} predicting {move}, expected {expected_move}")
                    errors += 1
                matched = True
                break
        if not matched:
            print(f"ERROR: State {state} was not covered by any pattern!")
            errors += 1
    
    if errors == 0:
        print("Verification passed! The advanced reduced list perfectly matches the original logic.\n")
        
    print("REDUCED_O_MOVE_LOOKUP = {")
    for pat, move in reduced_list:
        # Format the output beautifully 
        pat_str = f"('{pat[0]}', '{pat[1]}', '{pat[2]}', '{pat[3]}', '{pat[4]}', '{pat[5]}', '{pat[6]}', '{pat[7]}', '{pat[8]}')"
        print(f"    {pat_str}: {move},")
    print("}")
    # Save to JSON
    json_rules = {"".join(pat): move for pat, move in reduced_list}
    with open("minimized_rules.json", "w") as f:
        json.dump(json_rules, f, indent=4)
    print("Saved minimized rules to minimized_rules.json")
