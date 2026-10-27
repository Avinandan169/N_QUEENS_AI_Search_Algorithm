"""
Chessboard visualization utility for terminal display.
"""

from typing import List, Optional


def format_board(board: Optional[List[int]], n: int) -> str:
    """Formats an N-Queens board into a clean terminal ASCII representation.

    Args:
        board: 1D list where index = column and value = row. If None, indicates no solution.
        n: Dimension of the N x N board.

    Returns:
        A formatted multi-line string representing the chessboard.
    """
    if board is None:
        return f"No chessboard to display (N = {n}: No solution found or unsolvable)."

    lines = [f"N = {n}\n"]

    # Calculate padding width for coordinates based on number of digits
    row_width = len(str(n - 1))
    col_width = max(row_width, 1)

    # Column header
    header_prefix = " " * (row_width + 1)
    col_headers = [f"{c:>{col_width}}" for c in range(n)]
    lines.append(header_prefix + " ".join(col_headers))

    # Grid rows
    for r in range(n):
        row_str = f"{r:>{row_width}} "
        cells = []
        for c in range(n):
            if c < len(board) and board[c] == r:
                cells.append(f"{'Q':>{col_width}}")
            else:
                cells.append(f"{'.':>{col_width}}")
        row_str += " ".join(cells)
        lines.append(row_str)

    return "\n".join(lines)


def print_board(board: Optional[List[int]], n: int) -> None:
    """Print the formatted board directly to the terminal."""
    print(format_board(board, n))
