"""
Search event definitions for step-by-step AI algorithm visualization.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.metrics import SearchResult


@dataclass
class SearchEvent:
    """Represents a discrete, observable event emitted during search execution.

    Attributes:
        event_type: Category of the event (e.g., 'INIT', 'MOVE', 'LOCAL_MINIMUM',
            'PLATEAU', 'RESTART', 'EXPAND', 'GENERATE', 'TEST_ASSIGNMENT',
            'COMMIT_ASSIGNMENT', 'REJECT_ASSIGNMENT', 'BACKTRACK', 'GOAL',
            'BUDGET_EXHAUSTED', 'NO_SOLUTION_EXISTS').
        board: Board state as a list of length N, where board[col] is the row index,
            or None if the column is currently unassigned (partial board).
        description: Human-readable narrative of the algorithmic action for the event log.
        metrics: Current operational metrics (steps, expansions, assignments, backtracks, etc.).
        highlight_cell: Optional (row, col) coordinate to highlight visually on the chessboard.
        cell_status: Semantic state of the highlighted cell ('placed', 'moved', 'testing',
            'conflict', 'backtrack', 'expanded').
        domains: Optional mapping of unassigned variable columns to their remaining legal row sets.
        g: Path cost accumulated so far (for A*).
        h: Heuristic estimate of remaining cost / conflicts.
        f: Total evaluation function f(n) = g(n) + h(n) (for A*).
        frontier_size: Number of nodes currently waiting in the priority queue (for A*).
        current_state_tuple: Tuple representation of partial state (for A*).
        recent_children: List of recently generated successor states (for A*).
        recent_expanded: List of recently expanded states (for A*).
        is_terminal: True if the search has terminated (success, unsolvable, or budget exhausted).
        result: Final SearchResult object when is_terminal is True.
    """

    event_type: str
    board: Optional[List[Optional[int]]]
    description: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    highlight_cell: Optional[Tuple[int, int]] = None
    cell_status: Optional[str] = None
    domains: Optional[Dict[int, Set[int]]] = None
    g: Optional[int] = None
    h: Optional[int] = None
    f: Optional[int] = None
    frontier_size: Optional[int] = None
    current_state_tuple: Optional[Tuple[int, ...]] = None
    recent_children: Optional[List[str]] = None
    recent_expanded: Optional[List[str]] = None
    is_terminal: bool = False
    result: Optional[SearchResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the event into a JSON-serializable dictionary."""
        domains_serializable = None
        if self.domains is not None:
            domains_serializable = {
                str(col): sorted(list(rows)) for col, rows in self.domains.items()
            }

        return {
            "event_type": self.event_type,
            "board": self.board,
            "description": self.description,
            "metrics": self.metrics,
            "highlight_cell": list(self.highlight_cell) if self.highlight_cell else None,
            "cell_status": self.cell_status,
            "domains": domains_serializable,
            "g": self.g,
            "h": self.h,
            "f": self.f,
            "frontier_size": self.frontier_size,
            "current_state_tuple": list(self.current_state_tuple) if self.current_state_tuple else None,
            "recent_children": self.recent_children,
            "recent_expanded": self.recent_expanded,
            "is_terminal": self.is_terminal,
            "status": self.result.status if self.result else None,
            "is_valid": self.result.is_valid if self.result else None,
            "conflicts": self.result.conflicts if self.result else (self.h if self.h is not None else 0),
        }
