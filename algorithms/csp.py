"""
Constraint Satisfaction Problem (CSP) solver for N-Queens with MRV and Forward Checking.

Educational Overview:
---------------------
A Constraint Satisfaction Problem (CSP) formulates problems in terms of:
- Variables: X_0, X_1, ..., X_{N-1} (one variable per column).
- Domains: For each variable X_c, D(X_c) = {0, 1, ..., N - 1} (candidate rows).
- Constraints:
    For any distinct columns i and j:
      1. X_i != X_j (no two queens in the same row).
      2. |X_i - X_j| != |i - j| (no two queens on the same diagonal).

Differences from Other AI Paradigms:
-------------------------------------
- State-Space Search (e.g., A*): Treats states as monolithic nodes evaluated via f(n) = g(n) + h(n).
  The search tree branches over arbitrary state transitions without inspecting variable sub-structure.
- Local Search (e.g., Hill Climbing): Operates on complete assignments (all variables assigned),
  evaluating a global conflict heuristic h(n) and moving locally. It can get trapped in local minima
  and cannot systematically prove insolvability.
- CSP Search: Exploits the internal structure of variables, domains, and constraints.
  Using domain filtering (Forward Checking) and intelligent variable ordering (MRV),
  CSP prunes large subtrees before visiting them, achieving superior efficiency.

Techniques Implemented:
-----------------------
1. Backtracking Search: Depth-first recursive assignment of variables.
2. Minimum Remaining Values (MRV): Among unassigned columns, select the variable with the smallest
   remaining domain. This "fail-first" heuristic prunes dead ends earliest.
3. Forward Checking: Whenever variable X_c is assigned row r, immediately prune conflicting rows
   from the domains of all unassigned variables. If any domain becomes empty (domain wipeout),
   the branch fails immediately without wasting further depth.
4. Exact Domain Restoration: Pruned values are tracked per assignment level and restored
   symmetrically upon backtracking.
"""

import time
from typing import Dict, Generator, List, Optional, Set, Tuple

from utils.events import SearchEvent
from utils.metrics import SearchResult
from utils.validation import count_conflicts, validate_solution


class CSPSolver:
    """Encapsulates the CSP solver state and tracking counters."""

    def __init__(self, n: int):
        self.n = n
        self.variables = list(range(n))
        # Initial domain for each column is all rows 0..n-1
        self.domains: Dict[int, Set[int]] = {col: set(range(n)) for col in range(n)}
        self.assignment: Dict[int, int] = {}

        # Operational metrics
        self.assignments_count = 0
        self.backtracks_count = 0
        self.constraint_checks_count = 0

    def select_unassigned_variable(self) -> int:
        """Selects the unassigned variable with the Minimum Remaining Values (MRV).

        In case of ties in domain size, breaks ties by lowest column index.

        Returns:
            The selected column index.
        """
        unassigned_vars = [v for v in self.variables if v not in self.assignment]
        # Sort key: domain size first (MRV), then column index (tie-breaker)
        return min(unassigned_vars, key=lambda v: (len(self.domains[v]), v))

    def forward_check(
        self, assigned_col: int, assigned_row: int
    ) -> Optional[Dict[int, List[int]]]:
        """Prunes conflicting values from unassigned variables' domains.

        Args:
            assigned_col: Column of the newly assigned queen.
            assigned_row: Row of the newly assigned queen.

        Returns:
            A dictionary mapping each affected variable to the list of pruned rows,
            or None if a domain wipeout occurred (triggering immediate backtrack).
        """
        pruned: Dict[int, List[int]] = {}

        for unassigned_col in self.variables:
            if unassigned_col in self.assignment:
                continue

            col_dist = abs(unassigned_col - assigned_col)
            conflicting_values: List[int] = []

            for candidate_row in self.domains[unassigned_col]:
                self.constraint_checks_count += 1
                # Row conflict: same row
                # Diagonal conflict: |row1 - row2| == |col1 - col2|
                if (
                    candidate_row == assigned_row
                    or abs(candidate_row - assigned_row) == col_dist
                ):
                    conflicting_values.append(candidate_row)

            if conflicting_values:
                for val in conflicting_values:
                    self.domains[unassigned_col].remove(val)
                pruned[unassigned_col] = conflicting_values

                # Domain Wipeout: No valid values left for this unassigned variable
                if not self.domains[unassigned_col]:
                    # Restore whatever was pruned so far in this step and signal failure
                    self.restore_domains(pruned)
                    return None

        return pruned

    def restore_domains(self, pruned: Dict[int, List[int]]) -> None:
        """Restores values pruned during forward checking back into their respective domains."""
        for var, values in pruned.items():
            self.domains[var].update(values)

    def get_partial_board(self) -> List[Optional[int]]:
        """Returns the current board state as a list of length N (None for unassigned cols)."""
        return [self.assignment.get(c) for c in range(self.n)]

    def backtrack_generator(self) -> Generator[SearchEvent, None, bool]:
        """Generator performing recursive backtracking while yielding discrete search events.

        Yields:
            SearchEvent instances for MRV variable selection, candidate testing,
            forward checking pruning, commits, rejections, and backtracks.

        Returns:
            True if a complete valid assignment was found, False otherwise.
        """
        # Base case: All variables assigned
        if len(self.assignment) == self.n:
            return True

        # Variable selection using MRV
        var = self.select_unassigned_variable()
        candidate_rows = sorted(list(self.domains[var]))

        yield SearchEvent(
            event_type="SELECT_VARIABLE",
            board=self.get_partial_board(),
            description=(
                f"MRV selected Variable X_{var} (col {var}) with smallest domain size {len(candidate_rows)}: "
                f"candidates {candidate_rows}."
            ),
            metrics={
                "assignments": self.assignments_count,
                "backtracks": self.backtracks_count,
                "constraint_checks": self.constraint_checks_count,
            },
            domains={c: set(self.domains[c]) for c in self.variables if c not in self.assignment},
        )

        for row in candidate_rows:
            self.assignments_count += 1
            self.assignment[var] = row

            # Visual event: Testing assignment
            yield SearchEvent(
                event_type="TEST_ASSIGNMENT",
                board=self.get_partial_board(),
                description=f"Testing assignment: Queen at (row={row}, col={var}). Executing Forward Checking...",
                metrics={
                    "assignments": self.assignments_count,
                    "backtracks": self.backtracks_count,
                    "constraint_checks": self.constraint_checks_count,
                },
                highlight_cell=(row, var),
                cell_status="testing",
                domains={c: set(self.domains[c]) for c in self.variables if c not in self.assignment},
            )

            # Apply Forward Checking
            pruned = self.forward_check(var, row)

            if pruned is not None:
                # Forward checking succeeded
                pruned_summary = ", ".join(f"col {c}: pruned {vals}" for c, vals in pruned.items()) or "none"
                yield SearchEvent(
                    event_type="COMMIT_ASSIGNMENT",
                    board=self.get_partial_board(),
                    description=f"Committed assignment: Queen at (row={row}, col={var}). Pruned values: {pruned_summary}.",
                    metrics={
                        "assignments": self.assignments_count,
                        "backtracks": self.backtracks_count,
                        "constraint_checks": self.constraint_checks_count,
                    },
                    highlight_cell=(row, var),
                    cell_status="placed",
                    domains={c: set(self.domains[c]) for c in self.variables if c not in self.assignment},
                )

                sub_success = yield from self.backtrack_generator()
                if sub_success:
                    return True

                # Recursive call failed: Backtrack
                self.backtracks_count += 1
                self.restore_domains(pruned)
                del self.assignment[var]

                yield SearchEvent(
                    event_type="BACKTRACK",
                    board=self.get_partial_board(),
                    description=f"Backtracked from (row={row}, col={var}). Restored pruned domains.",
                    metrics={
                        "assignments": self.assignments_count,
                        "backtracks": self.backtracks_count,
                        "constraint_checks": self.constraint_checks_count,
                    },
                    highlight_cell=(row, var),
                    cell_status="backtrack",
                    domains={c: set(self.domains[c]) for c in self.variables if c not in self.assignment},
                )
            else:
                # Forward checking detected domain wipeout
                self.backtracks_count += 1
                del self.assignment[var]

                yield SearchEvent(
                    event_type="REJECT_ASSIGNMENT",
                    board=self.get_partial_board(),
                    description=f"Rejected assignment (row={row}, col={var}): Domain wipeout on unassigned variable! Backtracking...",
                    metrics={
                        "assignments": self.assignments_count,
                        "backtracks": self.backtracks_count,
                        "constraint_checks": self.constraint_checks_count,
                    },
                    highlight_cell=(row, var),
                    cell_status="conflict",
                    domains={c: set(self.domains[c]) for c in self.variables if c not in self.assignment},
                )

        return False

    def backtrack(self) -> bool:
        """Executes recursive backtracking with MRV and Forward Checking without yielding events."""
        if len(self.assignment) == self.n:
            return True

        var = self.select_unassigned_variable()
        candidate_rows = sorted(list(self.domains[var]))

        for row in candidate_rows:
            self.assignments_count += 1
            self.assignment[var] = row

            pruned = self.forward_check(var, row)
            if pruned is not None:
                if self.backtrack():
                    return True
                self.backtracks_count += 1
                self.restore_domains(pruned)
            else:
                self.backtracks_count += 1

            del self.assignment[var]

        return False


def csp_generator(n: int) -> Generator[SearchEvent, None, SearchResult]:
    """Generator yielding real-time search events during CSP search.

    Args:
        n: Board dimension (N x N).

    Yields:
        SearchEvent instances for variable selections, assignments, prunings, and backtracks.

    Returns:
        The final SearchResult object.
    """
    start_time = time.perf_counter()

    if n <= 0:
        res = SearchResult(
            algorithm_name="CSP (MRV + Forward Checking)",
            n=n,
            solution=None,
            is_valid=False,
            execution_time_seconds=time.perf_counter() - start_time,
            status="FAILURE",
            conflicts=-1,
            notes="Invalid board size N <= 0.",
        )
        yield SearchEvent(
            event_type="FAILURE",
            board=None,
            description="Invalid board size N <= 0.",
            metrics={"assignments": 0, "backtracks": 0},
            is_terminal=True,
            result=res,
        )
        return res

    if n == 1:
        elapsed = time.perf_counter() - start_time
        res = SearchResult(
            algorithm_name="CSP (MRV + Forward Checking)",
            n=1,
            solution=[0],
            is_valid=True,
            execution_time_seconds=elapsed,
            status="SUCCESS",
            conflicts=0,
            metrics={"assignments": 1, "backtracks": 0, "constraint_checks": 0},
            notes="Trivially solved for N = 1.",
        )
        yield SearchEvent(
            event_type="GOAL",
            board=[0],
            description="Trivially solved for N = 1: Single queen assigned at (0, 0).",
            metrics={"assignments": 1, "backtracks": 0, "constraint_checks": 0},
            highlight_cell=(0, 0),
            cell_status="placed",
            is_terminal=True,
            result=res,
        )
        return res

    solver = CSPSolver(n)
    success = yield from solver.backtrack_generator()
    elapsed = time.perf_counter() - start_time

    if success:
        solution = [solver.assignment[c] for c in range(n)]
        is_valid, _ = validate_solution(solution, n)
        res = SearchResult(
            algorithm_name="CSP (MRV + Forward Checking)",
            n=n,
            solution=solution,
            is_valid=is_valid,
            execution_time_seconds=elapsed,
            status="SUCCESS",
            conflicts=0,
            metrics={
                "assignments": solver.assignments_count,
                "backtracks": solver.backtracks_count,
                "constraint_checks": solver.constraint_checks_count,
            },
            notes="Solution found via MRV and Forward Checking.",
        )
        yield SearchEvent(
            event_type="GOAL",
            board=solution,  # type: ignore[arg-type]
            description=f"Goal reached! All {n} queens assigned without conflict via MRV & Forward Checking.",
            metrics={
                "assignments": solver.assignments_count,
                "backtracks": solver.backtracks_count,
                "constraint_checks": solver.constraint_checks_count,
            },
            highlight_cell=(solution[-1], n - 1),
            cell_status="placed",
            is_terminal=True,
            result=res,
        )
        return res
    else:
        status = "NO_SOLUTION_EXISTS" if n in (2, 3) else "FAILURE"
        unsolvable_note = (
            f"Mathematically proven: No solution exists for N = {n}."
            if n in (2, 3)
            else "Exhaustive search completed; no solution exists."
        )
        res = SearchResult(
            algorithm_name="CSP (MRV + Forward Checking)",
            n=n,
            solution=None,
            is_valid=False,
            execution_time_seconds=elapsed,
            status=status,
            conflicts=-1,
            metrics={
                "assignments": solver.assignments_count,
                "backtracks": solver.backtracks_count,
                "constraint_checks": solver.constraint_checks_count,
            },
            notes=unsolvable_note,
        )
        yield SearchEvent(
            event_type=status,
            board=None,
            description=f"Search ended: {status}. Exhaustive backtracking completed without valid placement.",
            metrics={
                "assignments": solver.assignments_count,
                "backtracks": solver.backtracks_count,
                "constraint_checks": solver.constraint_checks_count,
            },
            is_terminal=True,
            result=res,
        )
        return res


def solve_csp(n: int) -> SearchResult:
    """Solves the N-Queens problem using CSP with MRV and Forward Checking.

    Maintains backwards compatibility by running the event generator to completion.

    Args:
        n: Board dimension (N x N).

    Returns:
        SearchResult containing the final board, validity flag, timing, and operational metrics.
    """
    gen = csp_generator(n=n)
    last_res: Optional[SearchResult] = None
    for event in gen:
        if event.is_terminal and event.result is not None:
            last_res = event.result
    return last_res  # type: ignore[return-value]
