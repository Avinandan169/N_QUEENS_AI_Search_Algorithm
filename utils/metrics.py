"""
Data structures for standardized algorithm metrics and search results.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    """Represents the standardized result of an N-Queens search algorithm.

    Attributes:
        algorithm_name: Name of the algorithm used.
        n: Board size (N x N).
        solution: List of row positions for each column, or None if no solution found.
        is_valid: Whether the solution passes independent constraint validation.
        execution_time_seconds: Total wall-clock time spent in seconds.
        status: High-level status ('SUCCESS', 'NO_SOLUTION_EXISTS', 'BUDGET_EXHAUSTED', 'FAILURE').
        conflicts: Number of attacking pairs in the returned state (0 for valid solution).
        metrics: Algorithm-specific operational counters (steps, nodes, backtracks, etc.).
        notes: Contextual notes, such as theoretical limits or memory observations.
    """

    algorithm_name: str
    n: int
    solution: Optional[List[int]]
    is_valid: bool
    execution_time_seconds: float
    status: str
    conflicts: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
