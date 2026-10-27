"""
Independent solution validation and conflict calculation for the N-Queens problem.
"""

from typing import List, Optional, Tuple


def count_conflicts(board: List[int]) -> int:
    """Calculate the number of attacking queen pairs in a board configuration.

    In the 1D board representation, board[col] = row.
    Column conflicts are impossible because each column has exactly one queen.
    Two queens at (r1, c1) and (r2, c2) attack each other if:
      - r1 == r2 (same row)
      - abs(r1 - r2) == abs(c1 - c2) (same diagonal)

    Args:
        board: A list of integers representing queen row positions per column.

    Returns:
        The total number of mutually attacking pairs of queens.
    """
    conflicts = 0
    num_queens = len(board)

    for i in range(num_queens):
        row_i = board[i]
        for j in range(i + 1, num_queens):
            row_j = board[j]
            # Same row conflict
            if row_i == row_j:
                conflicts += 1
            # Diagonal conflict
            elif abs(row_i - row_j) == abs(i - j):
                conflicts += 1

    return conflicts


def validate_solution(board: Optional[List[int]], n: int) -> Tuple[bool, str]:
    """Independently verifies that a given board configuration is a valid N-Queens solution.

    Criteria:
      1. Board must not be None.
      2. Exactly N queens must be placed (len(board) == n).
      3. All row coordinates must be within [0, n - 1].
      4. No two queens share the same row.
      5. No two queens share the same column.
      6. No two queens share a diagonal.

    Args:
        board: A list of row indices for each column, or None.
        n: The expected board dimension N.

    Returns:
        A tuple of (is_valid, explanation_message).
    """
    if board is None:
        return False, "Validation failed: No board state provided (board is None)."

    if not isinstance(board, list):
        return False, f"Validation failed: Board must be a list, got {type(board).__name__}."

    if len(board) != n:
        return (
            False,
            f"Validation failed: Expected exactly {n} queens, but board has {len(board)} queens.",
        )

    for col, row in enumerate(board):
        if not isinstance(row, int):
            return (
                False,
                f"Validation failed: Row index at column {col} is not an integer: {row}.",
            )
        if row < 0 or row >= n:
            return (
                False,
                f"Validation failed: Queen at column {col} is placed at invalid row {row} (must be in 0..{n - 1}).",
            )

    # Check for row conflicts
    if len(set(board)) != n:
        # Find the specific row with multiple queens for clarity
        seen_rows = set()
        duplicate_rows = set()
        for r in board:
            if r in seen_rows:
                duplicate_rows.add(r)
            seen_rows.add(r)
        return (
            False,
            f"Validation failed: Multiple queens share the same row(s): {sorted(list(duplicate_rows))}.",
        )

    # Check for diagonal conflicts
    for i in range(n):
        for j in range(i + 1, n):
            if abs(board[i] - board[j]) == abs(i - j):
                return (
                    False,
                    f"Validation failed: Diagonal conflict between queen at (row={board[i]}, col={i}) "
                    f"and queen at (row={board[j]}, col={j}).",
                )

    return True, "Solution is valid: Exactly N non-attacking queens placed."
