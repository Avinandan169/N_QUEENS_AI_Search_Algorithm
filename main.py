"""
Command-Line Interface (CLI) for the N-Queens AI Solver.

Provides an interactive console menu for running:
1. Simple Hill Climbing (First-Choice)
2. Steepest-Ascent Hill Climbing
3. A* Search
4. CSP with Backtracking
5. Comparison of Algorithms
6. Launch Web Application
"""

import sys
from typing import Optional, Tuple

from algorithms.astar import solve_astar
from algorithms.csp import solve_csp
from algorithms.hill_climbing import (
    solve_simple_hill_climbing,
    solve_steepest_hill_climbing,
)
from utils.board import print_board
from utils.comparison import format_comparison_table, run_all_algorithms
from utils.metrics import SearchResult
from utils.validation import validate_solution


def prompt_board_size() -> int:
    """Prompts the user for board size N with input validation."""
    while True:
        try:
            raw_input = input("Enter board size N (e.g., 4, 8): ").strip()
            if not raw_input:
                print("Error: Input cannot be empty. Please enter an integer.")
                continue
            n = int(raw_input)
            if n <= 0:
                print("Error: Board size N must be a positive integer (N >= 1).")
                continue
            return n
        except ValueError:
            print("Error: Invalid input. Please enter a valid whole number.")


def prompt_hill_climbing_params() -> Tuple[int, int, Optional[int]]:
    """Prompts the user for optional Hill Climbing parameters with sensible defaults."""
    print("\n--- Hill Climbing Configuration ---")
    print("Press Enter to accept standard defaults.")

    max_restarts = 100
    raw_restarts = input(f"Max restarts [{max_restarts}]: ").strip()
    if raw_restarts and raw_restarts.isdigit():
        max_restarts = int(raw_restarts)

    max_steps = 500
    raw_steps = input(f"Max steps per restart [{max_steps}]: ").strip()
    if raw_steps and raw_steps.isdigit():
        max_steps = int(raw_steps)

    seed: Optional[int] = None
    raw_seed = input("Random seed (integer or press Enter for non-deterministic) [None]: ").strip()
    if raw_seed and (raw_seed.isdigit() or (raw_seed.startswith("-") and raw_seed[1:].isdigit())):
        seed = int(raw_seed)

    return max_restarts, max_steps, seed


def display_result(result: SearchResult) -> None:
    """Presents a standardized search result and chessboard display."""
    print("\n" + "=" * 50)
    print(f"ALGORITHM: {result.algorithm_name}")
    print(f"BOARD SIZE: N = {result.n}")
    print(f"STATUS: {result.status}")
    print(f"EXECUTION TIME: {result.execution_time_seconds * 1000.0:.3f} ms ({result.execution_time_seconds:.6f} s)")
    print(f"CONFLICTS IN FINAL STATE: {result.conflicts}")

    print("\nMETRICS:")
    for key, value in result.metrics.items():
        formatted_val = f"{value:,}" if isinstance(value, int) else value
        print(f"  - {key.replace('_', ' ').capitalize()}: {formatted_val}")

    if result.notes:
        print(f"\nNOTES: {result.notes}")

    print("\nVALIDATION:")
    if result.solution is not None:
        is_valid, reason = validate_solution(result.solution, result.n)
        print(f"  [{'PASSED' if is_valid else 'FAILED'}] {reason}")
    else:
        print("  [N/A] No solution board returned to validate.")

    print("\nCHESSBOARD:")
    print_board(result.solution, result.n)
    print("=" * 50)


def run_simple_hc_menu() -> None:
    n = prompt_board_size()
    restarts, steps, seed = prompt_hill_climbing_params()
    print(f"\nExecuting Simple Hill Climbing (First-Choice) for N = {n}...")
    res = solve_simple_hill_climbing(n, restarts, steps, seed)
    display_result(res)


def run_steepest_hc_menu() -> None:
    n = prompt_board_size()
    restarts, steps, seed = prompt_hill_climbing_params()
    print(f"\nExecuting Steepest-Ascent Hill Climbing for N = {n}...")
    res = solve_steepest_hill_climbing(n, restarts, steps, seed)
    display_result(res)


def run_astar_menu() -> None:
    n = prompt_board_size()
    if n > 12:
        print(f"\n[CAUTION] A* Search memory scales exponentially. Max node limit active.")
    print(f"\nExecuting A* Search for N = {n}...")
    res = solve_astar(n)
    display_result(res)


def run_csp_menu() -> None:
    n = prompt_board_size()
    print(f"\nExecuting CSP (MRV + Forward Checking) for N = {n}...")
    res = solve_csp(n)
    display_result(res)


def run_comparison_menu() -> None:
    n = prompt_board_size()
    print(f"\nRunning benchmark comparison for N = {n}...")
    results = run_all_algorithms(n, hc_seed=42)
    print(format_comparison_table(results))
    for res in results:
        if res.solution is not None and res.is_valid:
            print(f"\nSample Valid Board ({res.algorithm_name}):")
            print_board(res.solution, n)
            break


def launch_web_app() -> None:
    from server import run_server
    run_server(port=8000, auto_open=True)


def main() -> None:
    """Main CLI entry point."""
    if "--web" in sys.argv or "-w" in sys.argv:
        launch_web_app()
        return

    menu_text = """
========== N-QUEENS SOLVER ==========

1. Simple Hill Climbing (First-Choice)
2. Steepest-Ascent Hill Climbing
3. A* Search
4. CSP with Backtracking
5. Compare Algorithms
6. Launch Web Application
7. Exit
"""
    while True:
        print(menu_text)
        try:
            choice = input("Select an option (1-7): ").strip().lower()
            if not choice:
                continue

            if choice == "1":
                run_simple_hc_menu()
            elif choice == "2":
                run_steepest_hc_menu()
            elif choice == "3":
                run_astar_menu()
            elif choice == "4":
                run_csp_menu()
            elif choice == "5":
                run_comparison_menu()
            elif choice in ("6", "web"):
                launch_web_app()
            elif choice in ("7", "exit", "quit", "q"):
                print("\nExiting N-Queens Solver. Goodbye!\n")
                sys.exit(0)
            else:
                print("Error: Invalid option. Please select 1 through 7.")
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession terminated by user. Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
