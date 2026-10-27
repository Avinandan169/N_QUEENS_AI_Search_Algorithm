"""
A* Search algorithm for the N-Queens problem.

Educational Overview:
---------------------
A* is an informed tree/graph search algorithm that explores states in order of their
estimated total path cost:
    f(n) = g(n) + h(n)

In this N-Queens formulation:
- Search Tree: Successive columns from 0 to N - 1. Each level k places a queen in column k.
- State Representation: A tuple of row positions for queens placed so far:
  e.g., (1, 3) means queen 0 is at row 1, queen 1 is at row 3.
- Constraint Pruning: Successor states violating row or diagonal constraints are immediately rejected.
- Cost Function g(n): Number of queens placed so far (each queen placement action costs 1).
- Heuristic h(n): N - len(state) (the number of remaining queens to be placed).
- Admissibility:
  A heuristic is admissible if h(n) <= h*(n) for all states n, where h*(n) is the true minimal
  remaining cost. Since each remaining queen costs 1 to place, reaching any complete placement
  of N queens requires at least N - len(state) placements. Thus, h(n) = N - len(state) <= h*(n).
  It is strictly admissible.
- Behavior and Limitations:
  Because g(n) + h(n) = k + (N - k) = N for every valid state, all candidate states share
  the exact same f-value (f = N). Consequently, f(n) provides no discriminatory guidance
  between states at the same depth; guidance is provided by constraint rejection and depth
  tie-breaking. Furthermore, storing the search frontier in memory causes exponential memory
  consumption O(b^d), making A* practical only for small N in this problem.
"""

import collections
import heapq
import time
from typing import Generator, List, Optional, Tuple

from utils.events import SearchEvent
from utils.metrics import SearchResult
from utils.validation import count_conflicts, validate_solution


def _is_safe_placement(placed_rows: Tuple[int, ...], new_col: int, new_row: int) -> bool:
    """Checks if placing a queen at (new_row, new_col) conflicts with already placed queens.

    Args:
        placed_rows: Tuple of row positions for previously placed columns 0..new_col - 1.
        new_col: The column index for the new queen.
        new_row: The row index for the new queen.

    Returns:
        True if the placement does not attack any previously placed queen, False otherwise.
    """
    for col, row in enumerate(placed_rows):
        # Same row conflict
        if row == new_row:
            return False
        # Diagonal conflict: |row1 - row2| == |col1 - col2|
        if abs(row - new_row) == abs(col - new_col):
            return False
    return True


def astar_generator(
    n: int,
    max_nodes: Optional[int] = 500_000,
) -> Generator[SearchEvent, None, SearchResult]:
    """Generator yielding real-time search events during A* Search execution.

    Args:
        n: Board dimension (N x N).
        max_nodes: Safety limit on total generated nodes to prevent Out-Of-Memory errors.

    Yields:
        SearchEvent instances capturing node expansions, child generations, frontier size,
        and goal/failure states.

    Returns:
        The final SearchResult object.
    """
    start_time = time.perf_counter()

    # Edge cases
    if n <= 0:
        res = SearchResult(
            algorithm_name="A* Search",
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
            metrics={"expanded_nodes": 0, "generated_nodes": 0},
            is_terminal=True,
            result=res,
        )
        return res

    if n == 1:
        elapsed = time.perf_counter() - start_time
        res = SearchResult(
            algorithm_name="A* Search",
            n=1,
            solution=[0],
            is_valid=True,
            execution_time_seconds=elapsed,
            status="SUCCESS",
            conflicts=0,
            metrics={"expanded_nodes": 1, "generated_nodes": 1, "frontier_peak": 1},
            notes="Trivially solved for N = 1.",
        )
        yield SearchEvent(
            event_type="GOAL",
            board=[0],
            description="Trivially solved for N = 1: Single queen placed at (0, 0).",
            metrics={"expanded_nodes": 1, "generated_nodes": 1, "frontier_size": 0},
            highlight_cell=(0, 0),
            cell_status="placed",
            g=1,
            h=0,
            f=1,
            is_terminal=True,
            result=res,
        )
        return res

    unsolvable_note = (
        f"Mathematically proven: No solution exists for N = {n}."
        if n in (2, 3)
        else ""
    )

    open_heap: List[Tuple[int, int, int, Tuple[int, ...]]] = []
    counter = 0

    # Initial empty state
    initial_state: Tuple[int, ...] = ()
    g_init = 0
    h_init = n
    f_init = g_init + h_init
    heapq.heappush(open_heap, (f_init, 0, counter, initial_state))
    counter += 1

    expanded_nodes = 0
    generated_nodes = 1
    frontier_peak = 1
    recent_expanded_history: collections.deque[str] = collections.deque(maxlen=6)

    while open_heap:
        frontier_peak = max(frontier_peak, len(open_heap))

        if max_nodes is not None and generated_nodes >= max_nodes:
            elapsed = time.perf_counter() - start_time
            res = SearchResult(
                algorithm_name="A* Search",
                n=n,
                solution=None,
                is_valid=False,
                execution_time_seconds=elapsed,
                status="BUDGET_EXHAUSTED",
                conflicts=-1,
                metrics={
                    "expanded_nodes": expanded_nodes,
                    "generated_nodes": generated_nodes,
                    "frontier_peak": frontier_peak,
                },
                notes=f"Generated node budget ({max_nodes}) exceeded. A* memory frontier saturated.",
            )
            yield SearchEvent(
                event_type="BUDGET_EXHAUSTED",
                board=None,
                description=f"A* Search budget exhausted: frontier saturated at {max_nodes} generated nodes.",
                metrics={
                    "expanded_nodes": expanded_nodes,
                    "generated_nodes": generated_nodes,
                    "frontier_size": len(open_heap),
                },
                is_terminal=True,
                result=res,
            )
            return res

        f_val, neg_depth, _, current_state = heapq.heappop(open_heap)
        expanded_nodes += 1
        current_depth = len(current_state)

        # Build partial board representation: assigned columns get row index, rest are None
        partial_board: List[Optional[int]] = [
            current_state[c] if c < current_depth else None for c in range(n)
        ]

        recent_expanded_history.append(
            f"State {current_state} (depth={current_depth}, f={f_val})"
        )

        # Goal check: All N queens placed without conflict
        if current_depth == n:
            solution_list = list(current_state)
            elapsed = time.perf_counter() - start_time
            is_valid, _ = validate_solution(solution_list, n)
            res = SearchResult(
                algorithm_name="A* Search",
                n=n,
                solution=solution_list,
                is_valid=is_valid,
                execution_time_seconds=elapsed,
                status="SUCCESS",
                conflicts=0,
                metrics={
                    "expanded_nodes": expanded_nodes,
                    "generated_nodes": generated_nodes,
                    "frontier_peak": frontier_peak,
                },
                notes="Admissible A* search successfully reached goal depth N.",
            )
            yield SearchEvent(
                event_type="GOAL",
                board=solution_list,  # type: ignore[arg-type]
                description=f"Goal reached! All {n} queens safely placed at depth {n} with f(n) = {f_val}.",
                metrics={
                    "expanded_nodes": expanded_nodes,
                    "generated_nodes": generated_nodes,
                    "frontier_size": len(open_heap),
                },
                highlight_cell=(current_state[-1], n - 1),
                cell_status="placed",
                g=n,
                h=0,
                f=f_val,
                frontier_size=len(open_heap),
                current_state_tuple=current_state,
                recent_expanded=list(recent_expanded_history),
                is_terminal=True,
                result=res,
            )
            return res

        # Generate successors in next column
        next_col = current_depth
        child_descriptions: List[str] = []

        for candidate_row in range(n):
            if _is_safe_placement(current_state, next_col, candidate_row):
                successor_state = current_state + (candidate_row,)
                g_succ = len(successor_state)
                h_succ = n - len(successor_state)
                f_succ = g_succ + h_succ

                heapq.heappush(
                    open_heap,
                    (f_succ, -len(successor_state), counter, successor_state),
                )
                counter += 1
                generated_nodes += 1
                child_descriptions.append(
                    f"col {next_col}->row {candidate_row} (g={g_succ}, h={h_succ}, f={f_succ})"
                )

        last_placed_coord = (
            (current_state[-1], current_depth - 1) if current_depth > 0 else None
        )

        yield SearchEvent(
            event_type="EXPAND",
            board=partial_board,
            description=(
                f"Popped node from priority queue: state {current_state}. "
                f"Depth={current_depth}, g={current_depth}, h={n - current_depth}, f={f_val}. "
                f"Generated {len(child_descriptions)} safe child state(s)."
            ),
            metrics={
                "expanded_nodes": expanded_nodes,
                "generated_nodes": generated_nodes,
                "frontier_size": len(open_heap),
                "frontier_peak": frontier_peak,
            },
            highlight_cell=last_placed_coord,
            cell_status="expanded" if last_placed_coord else None,
            g=current_depth,
            h=n - current_depth,
            f=f_val,
            frontier_size=len(open_heap),
            current_state_tuple=current_state,
            recent_children=child_descriptions,
            recent_expanded=list(recent_expanded_history),
        )

    # Frontier exhausted without finding a goal
    elapsed = time.perf_counter() - start_time
    status = "NO_SOLUTION_EXISTS" if n in (2, 3) else "FAILURE"

    res = SearchResult(
        algorithm_name="A* Search",
        n=n,
        solution=None,
        is_valid=False,
        execution_time_seconds=elapsed,
        status=status,
        conflicts=-1,
        metrics={
            "expanded_nodes": expanded_nodes,
            "generated_nodes": generated_nodes,
            "frontier_peak": frontier_peak,
        },
        notes=unsolvable_note or "Frontier exhausted with no valid assignment found.",
    )

    yield SearchEvent(
        event_type=status,
        board=None,
        description=f"A* Search terminated: {status}. Frontier exhausted.",
        metrics={
            "expanded_nodes": expanded_nodes,
            "generated_nodes": generated_nodes,
            "frontier_size": 0,
        },
        is_terminal=True,
        result=res,
    )
    return res


def solve_astar(
    n: int,
    max_nodes: Optional[int] = 500_000,
) -> SearchResult:
    """Solves the N-Queens problem using A* Search with priority queue.

    Maintains backwards compatibility by running the event generator to completion.

    Args:
        n: Board dimension (N x N).
        max_nodes: Safety limit on total generated nodes to prevent Out-Of-Memory errors.

    Returns:
        SearchResult containing the final board, validity flag, timing, and operational metrics.
    """
    gen = astar_generator(n=n, max_nodes=max_nodes)
    last_res: Optional[SearchResult] = None
    for event in gen:
        if event.is_terminal and event.result is not None:
            last_res = event.result
    return last_res  # type: ignore[return-value]
