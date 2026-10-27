"""
Simple Hill Climbing and Steepest-Ascent Hill Climbing algorithms for N-Queens.

Educational Comparison:
-----------------------
1. Simple Hill Climbing (First-Choice / Greedy Local Search):
   - Starts with a complete board (1 queen per column).
   - Iterates through neighbors in a consistent order: column 0..N-1, row 0..N-1.
   - Accepts the FIRST neighbor that strictly reduces conflicts (h < current_h).
   - Moves immediately without evaluating remaining neighbors.
   - Fast per step, but takes smaller improvement gradients.

2. Steepest-Ascent Hill Climbing:
   - Starts with a complete board (1 queen per column).
   - Evaluates ALL N * (N - 1) possible single-queen moves.
   - Selects the neighbor that yields the greatest reduction in conflicts.
   - Uses a deterministic tie-breaker (lowest column, lowest row).
   - More computationally intensive per step, but follows the steepest descent gradient.

Both algorithms detect local minima and plateaus when no improving neighbor exists,
and use random restarts to sample new regions of the state space.
"""

import random
import time
from typing import Generator, List, Optional, Tuple

from utils.events import SearchEvent
from utils.metrics import SearchResult
from utils.validation import count_conflicts, validate_solution


def simple_hill_climbing_generator(
    n: int,
    max_restarts: int = 100,
    max_steps_per_restart: int = 500,
    random_seed: Optional[int] = None,
) -> Generator[SearchEvent, None, SearchResult]:
    """Yields real-time events for Simple Hill Climbing (first improving neighbor)."""
    start_time = time.perf_counter()
    rng = random.Random(random_seed)

    if n <= 0:
        res = SearchResult("Simple Hill Climbing", n, None, False, time.perf_counter() - start_time, "FAILURE", -1, notes="Invalid N <= 0.")
        yield SearchEvent("FAILURE", None, "Invalid board size N <= 0.", is_terminal=True, result=res)
        return res

    if n == 1:
        elapsed = time.perf_counter() - start_time
        res = SearchResult("Simple Hill Climbing", 1, [0], True, elapsed, "SUCCESS", 0, {"steps": 0, "restarts": 0, "heuristic_evaluations": 1})
        yield SearchEvent("GOAL", [0], "Trivially solved for N = 1.", highlight_cell=(0, 0), cell_status="placed", h=0, is_terminal=True, result=res)
        return res

    notes = f"Mathematically proven: No solution exists for N = {n}." if n in (2, 3) else ""
    total_steps = 0
    total_restarts = 0
    heuristic_evaluations = 0

    best_overall_board: Optional[List[int]] = None
    best_overall_h = float("inf")

    for restart_idx in range(max_restarts + 1):
        if restart_idx > 0:
            total_restarts += 1
            yield SearchEvent(
                "RESTART",
                list(best_overall_board) if best_overall_board else None,
                f"Simple HC Restart #{total_restarts}: Escaping local optimum (Best so far: h = {best_overall_h}).",
                {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations, "h": int(best_overall_h)},
                h=int(best_overall_h),
            )

        current_board = [rng.randint(0, n - 1) for _ in range(n)]
        current_h = count_conflicts(current_board)
        heuristic_evaluations += 1

        if current_h < best_overall_h:
            best_overall_h = current_h
            best_overall_board = list(current_board)

        yield SearchEvent(
            "INIT",
            list(current_board),
            f"Simple HC Restart {total_restarts}: Generated random board with h = {current_h} conflicts.",
            {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations, "h": current_h},
            h=current_h,
        )

        if current_h == 0:
            elapsed = time.perf_counter() - start_time
            is_valid, _ = validate_solution(current_board, n)
            res = SearchResult("Simple Hill Climbing", n, current_board, is_valid, elapsed, "SUCCESS", 0, {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations})
            yield SearchEvent("GOAL", list(current_board), "Initial board is already a valid solution with 0 conflicts!", highlight_cell=(current_board[0], 0), cell_status="placed", h=0, is_terminal=True, result=res)
            return res

        step_in_restart = 0
        while step_in_restart < max_steps_per_restart:
            step_in_restart += 1
            total_steps += 1

            improving_move_found = False
            for col in range(n):
                orig_row = current_board[col]
                for new_row in range(n):
                    if new_row == orig_row:
                        continue

                    neighbor = list(current_board)
                    neighbor[col] = new_row
                    h = count_conflicts(neighbor)
                    heuristic_evaluations += 1

                    if h < current_h:
                        before_h = current_h
                        current_h = h
                        current_board = neighbor
                        improving_move_found = True

                        if current_h < best_overall_h:
                            best_overall_h = current_h
                            best_overall_board = list(current_board)

                        yield SearchEvent(
                            "MOVE",
                            list(current_board),
                            (
                                f"Simple HC Step {total_steps}: Found FIRST improving neighbor at col {col} (row {orig_row} -> {new_row}). "
                                f"Conflicts reduced: {before_h} -> {current_h}. Accepted immediately!"
                            ),
                            {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations, "h": current_h},
                            highlight_cell=(new_row, col),
                            cell_status="moved",
                            h=current_h,
                        )

                        if current_h == 0:
                            elapsed = time.perf_counter() - start_time
                            is_valid, _ = validate_solution(current_board, n)
                            res = SearchResult("Simple Hill Climbing", n, current_board, is_valid, elapsed, "SUCCESS", 0, {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations})
                            yield SearchEvent("GOAL", list(current_board), f"Simple HC solved! 0 conflicts reached at step {total_steps}.", highlight_cell=(new_row, col), cell_status="placed", h=0, is_terminal=True, result=res)
                            return res

                        break  # Move immediately on first improvement
                if improving_move_found:
                    break

            if not improving_move_found:
                # No neighbor improved: trapped in local minimum / plateau
                yield SearchEvent(
                    "LOCAL_MINIMUM",
                    list(current_board),
                    f"Simple HC trapped in local optimum at step {total_steps}: checked all neighbors, none improves h={current_h}.",
                    {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations, "h": current_h},
                    h=current_h,
                )
                break

    elapsed = time.perf_counter() - start_time
    is_valid, _ = validate_solution(best_overall_board, n)
    status = "NO_SOLUTION_EXISTS" if n in (2, 3) else "BUDGET_EXHAUSTED"
    res = SearchResult("Simple Hill Climbing", n, best_overall_board, is_valid, elapsed, status, int(best_overall_h), {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations}, notes=notes or "Budget exhausted.")
    yield SearchEvent(status, list(best_overall_board) if best_overall_board else None, f"Simple HC finished: {status} (Lowest h reached = {best_overall_h}).", is_terminal=True, result=res)
    return res


def steepest_hill_climbing_generator(
    n: int,
    max_restarts: int = 100,
    max_steps_per_restart: int = 500,
    random_seed: Optional[int] = None,
) -> Generator[SearchEvent, None, SearchResult]:
    """Yields real-time events for Steepest-Ascent Hill Climbing (evaluates all neighbors)."""
    start_time = time.perf_counter()
    rng = random.Random(random_seed)

    if n <= 0:
        res = SearchResult("Steepest-Ascent Hill Climbing", n, None, False, time.perf_counter() - start_time, "FAILURE", -1, notes="Invalid N <= 0.")
        yield SearchEvent("FAILURE", None, "Invalid board size N <= 0.", is_terminal=True, result=res)
        return res

    if n == 1:
        elapsed = time.perf_counter() - start_time
        res = SearchResult("Steepest-Ascent Hill Climbing", 1, [0], True, elapsed, "SUCCESS", 0, {"steps": 0, "restarts": 0, "heuristic_evaluations": 1})
        yield SearchEvent("GOAL", [0], "Trivially solved for N = 1.", highlight_cell=(0, 0), cell_status="placed", h=0, is_terminal=True, result=res)
        return res

    notes = f"Mathematically proven: No solution exists for N = {n}." if n in (2, 3) else ""
    total_steps = 0
    total_restarts = 0
    heuristic_evaluations = 0

    best_overall_board: Optional[List[int]] = None
    best_overall_h = float("inf")

    for restart_idx in range(max_restarts + 1):
        if restart_idx > 0:
            total_restarts += 1
            yield SearchEvent(
                "RESTART",
                list(best_overall_board) if best_overall_board else None,
                f"Steepest HC Restart #{total_restarts}: Escaping local optimum (Best so far: h = {best_overall_h}).",
                {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations, "h": int(best_overall_h)},
                h=int(best_overall_h),
            )

        current_board = [rng.randint(0, n - 1) for _ in range(n)]
        current_h = count_conflicts(current_board)
        heuristic_evaluations += 1

        if current_h < best_overall_h:
            best_overall_h = current_h
            best_overall_board = list(current_board)

        yield SearchEvent(
            "INIT",
            list(current_board),
            f"Steepest HC Restart {total_restarts}: Generated random board with h = {current_h} conflicts.",
            {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations, "h": current_h},
            h=current_h,
        )

        if current_h == 0:
            elapsed = time.perf_counter() - start_time
            is_valid, _ = validate_solution(current_board, n)
            res = SearchResult("Steepest-Ascent Hill Climbing", n, current_board, is_valid, elapsed, "SUCCESS", 0, {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations})
            yield SearchEvent("GOAL", list(current_board), "Initial board is already a valid solution with 0 conflicts!", highlight_cell=(current_board[0], 0), cell_status="placed", h=0, is_terminal=True, result=res)
            return res

        step_in_restart = 0
        while step_in_restart < max_steps_per_restart:
            step_in_restart += 1
            total_steps += 1

            best_neighbor_h = current_h
            best_neighbor = None
            best_col = -1
            best_orig_row = -1
            best_new_row = -1

            # Evaluate ALL N * (N - 1) neighbors
            for col in range(n):
                orig_row = current_board[col]
                for new_row in range(n):
                    if new_row == orig_row:
                        continue

                    neighbor = list(current_board)
                    neighbor[col] = new_row
                    h = count_conflicts(neighbor)
                    heuristic_evaluations += 1

                    # Deterministic tie-breaking: first strictly best neighbor encountered
                    if h < best_neighbor_h:
                        best_neighbor_h = h
                        best_neighbor = neighbor
                        best_col = col
                        best_orig_row = orig_row
                        best_new_row = new_row

            if best_neighbor is not None:
                before_h = current_h
                current_h = best_neighbor_h
                current_board = best_neighbor

                if current_h < best_overall_h:
                    best_overall_h = current_h
                    best_overall_board = list(current_board)

                yield SearchEvent(
                    "MOVE",
                    list(current_board),
                    (
                        f"Steepest HC Step {total_steps}: Evaluated all {n * (n - 1)} neighbors. "
                        f"Selected steepest drop at Queen col {best_col} (row {best_orig_row} -> {best_new_row}). "
                        f"Conflicts reduced: {before_h} -> {current_h}."
                    ),
                    {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations, "h": current_h},
                    highlight_cell=(best_new_row, best_col),
                    cell_status="moved",
                    h=current_h,
                )

                if current_h == 0:
                    elapsed = time.perf_counter() - start_time
                    is_valid, _ = validate_solution(current_board, n)
                    res = SearchResult("Steepest-Ascent Hill Climbing", n, current_board, is_valid, elapsed, "SUCCESS", 0, {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations})
                    yield SearchEvent("GOAL", list(current_board), f"Steepest HC solved! 0 conflicts reached at step {total_steps}.", highlight_cell=(best_new_row, best_col), cell_status="placed", h=0, is_terminal=True, result=res)
                    return res
            else:
                # No neighbor improved
                yield SearchEvent(
                    "LOCAL_MINIMUM",
                    list(current_board),
                    f"Steepest HC trapped in local optimum at step {total_steps}: evaluated all {n * (n - 1)} neighbors, none has h < {current_h}.",
                    {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations, "h": current_h},
                    h=current_h,
                )
                break

    elapsed = time.perf_counter() - start_time
    is_valid, _ = validate_solution(best_overall_board, n)
    status = "NO_SOLUTION_EXISTS" if n in (2, 3) else "BUDGET_EXHAUSTED"
    res = SearchResult("Steepest-Ascent Hill Climbing", n, best_overall_board, is_valid, elapsed, status, int(best_overall_h), {"steps": total_steps, "restarts": total_restarts, "heuristic_evaluations": heuristic_evaluations}, notes=notes or "Budget exhausted.")
    yield SearchEvent(status, list(best_overall_board) if best_overall_board else None, f"Steepest HC finished: {status} (Lowest h reached = {best_overall_h}).", is_terminal=True, result=res)
    return res


def solve_simple_hill_climbing(n: int, max_restarts: int = 100, max_steps_per_restart: int = 500, random_seed: Optional[int] = None) -> SearchResult:
    """Solves N-Queens using Simple Hill Climbing."""
    gen = simple_hill_climbing_generator(n, max_restarts, max_steps_per_restart, random_seed)
    last = None
    for event in gen:
        if event.is_terminal and event.result:
            last = event.result
    return last  # type: ignore[return-value]


def solve_steepest_hill_climbing(n: int, max_restarts: int = 100, max_steps_per_restart: int = 500, random_seed: Optional[int] = None) -> SearchResult:
    """Solves N-Queens using Steepest-Ascent Hill Climbing."""
    gen = steepest_hill_climbing_generator(n, max_restarts, max_steps_per_restart, random_seed)
    last = None
    for event in gen:
        if event.is_terminal and event.result:
            last = event.result
    return last  # type: ignore[return-value]


# Aliases for backwards compatibility
hill_climbing_generator = steepest_hill_climbing_generator
solve_hill_climbing = solve_steepest_hill_climbing
