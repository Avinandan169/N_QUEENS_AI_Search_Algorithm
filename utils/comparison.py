"""
Comparison utilities for evaluating and presenting multi-algorithm performance on N-Queens.
"""

from typing import List, Optional
from utils.metrics import SearchResult


def run_all_algorithms(
    n: int,
    hc_max_restarts: int = 100,
    hc_max_steps: int = 500,
    hc_seed: Optional[int] = None,
    astar_max_nodes: Optional[int] = 500_000,
) -> List[SearchResult]:
    """Runs Hill Climbing, A* Search, and CSP on the same board size N.

    Args:
        n: Board dimension.
        hc_max_restarts: Max restarts for Hill Climbing.
        hc_max_steps: Max steps per restart for Hill Climbing.
        hc_seed: Optional random seed for Hill Climbing.
        astar_max_nodes: Memory safety limit for A*.

    Returns:
        List of SearchResult objects [HC_result, Astar_result, CSP_result].
    """
    # Lazy imports avoid circular dependencies across packages
    from algorithms.hill_climbing import solve_hill_climbing
    from algorithms.astar import solve_astar
    from algorithms.csp import solve_csp

    results: List[SearchResult] = []

    # 1. Hill Climbing
    hc_res = solve_hill_climbing(
        n=n,
        max_restarts=hc_max_restarts,
        max_steps_per_restart=hc_max_steps,
        random_seed=hc_seed,
    )
    results.append(hc_res)

    # 2. A* Search
    astar_res = solve_astar(n=n, max_nodes=astar_max_nodes)
    results.append(astar_res)

    # 3. CSP with MRV and Forward Checking
    csp_res = solve_csp(n=n)
    results.append(csp_res)

    return results


def format_comparison_table(results: List[SearchResult]) -> str:
    """Formats a list of SearchResults into a clean, aligned ASCII comparison table.

    Args:
        results: List of SearchResult objects from different algorithms.

    Returns:
        Formatted multi-line comparison string.
    """
    rows = []
    for r in results:
        found_str = "Yes" if r.is_valid and r.status == "SUCCESS" else "No"
        time_str = f"{r.execution_time_seconds * 1000.0:.2f} ms"

        if r.algorithm_name.startswith("Hill Climbing"):
            explored_str = f"{r.metrics.get('steps', 0)} steps"
            restarts = r.metrics.get("restarts", 0)
            hevals = r.metrics.get("heuristic_evaluations", 0)
            spec_str = f"Restarts: {restarts} | H-Evals: {hevals:,}"
            scale_note = "Local search; fast but incomplete; needs restarts."
        elif r.algorithm_name.startswith("A*"):
            exp = r.metrics.get("expanded_nodes", 0)
            gen = r.metrics.get("generated_nodes", 0)
            peak = r.metrics.get("frontier_peak", 0)
            explored_str = f"{exp:,} exp / {gen:,} gen"
            spec_str = f"Frontier Peak: {peak:,} nodes"
            scale_note = "Exponential O(b^d) memory; practical only for small N (<=10)."
        elif r.algorithm_name.startswith("CSP"):
            assigns = r.metrics.get("assignments", 0)
            btracks = r.metrics.get("backtracks", 0)
            checks = r.metrics.get("constraint_checks", 0)
            explored_str = f"{assigns:,} assigns"
            spec_str = f"Backtracks: {btracks:,} | Checks: {checks:,}"
            scale_note = "Systematic domain pruning; highly scalable for large N."
        else:
            explored_str = "N/A"
            spec_str = "N/A"
            scale_note = r.notes

        rows.append(
            (
                r.algorithm_name,
                found_str,
                time_str,
                explored_str,
                spec_str,
                str(r.conflicts if r.conflicts >= 0 else "N/A"),
                scale_note,
            )
        )

    col_names = [
        "Algorithm",
        "Solution Found",
        "Time (ms)",
        "States Explored/Gen",
        "Specific Metrics",
        "Conflicts",
        "Scalability Notes",
    ]

    # Compute column widths
    widths = [len(h) for h in col_names]
    for row in rows:
        for idx, val in enumerate(row):
            widths[idx] = max(widths[idx], len(val))

    def make_divider(char: str = "-") -> str:
        parts = ["+" + char * (w + 2) for w in widths]
        return "".join(parts) + "+"

    header_line = (
        "| "
        + " | ".join(f"{col_names[i]:<{widths[i]}}" for i in range(len(col_names)))
        + " |"
    )

    out_lines = [
        f"\nAlgorithm Comparison for N = {results[0].n if results else 'N/A'}:",
        make_divider("-"),
        header_line,
        make_divider("="),
    ]

    for row in rows:
        row_line = (
            "| "
            + " | ".join(f"{row[i]:<{widths[i]}}" for i in range(len(row)))
            + " |"
        )
        out_lines.append(row_line)

    out_lines.append(make_divider("-"))

    # Educational notes on comparability
    comparability_notes = (
        "\nIMPORTANT METHODOLOGICAL NOTES ON METRIC COMPARABILITY:\n"
        "1. Search Space Discrepancy:\n"
        "   - Hill Climbing operates on complete board configurations (N queens placed, 1 per col).\n"
        "     Each step moves 1 queen and evaluates N*(N-1) neighbors.\n"
        "   - A* operates on partial configurations (depth 0 to N) in a tree search, storing an\n"
        "     in-memory priority queue frontier.\n"
        "   - CSP operates on variable domains using systematic backtracking with MRV heuristic\n"
        "     and forward checking constraint propagation.\n"
        "   Therefore, 'steps', 'expanded states', and 'assignments' reflect fundamentally different\n"
        "   units of search effort and cannot be directly equated.\n"
        "2. Algorithmic Work vs. Wall-Clock Time:\n"
        "   - Wall-clock time depends on Python interpreter overhead, garbage collection, and data\n"
        "     structure operations (e.g. heap manipulation vs. set intersection).\n"
        "   - Algorithmic counters (H-evaluations, nodes expanded, backtracks) provide machine-independent\n"
        "     measures of search work.\n"
    )
    out_lines.append(comparability_notes)

    return "\n".join(out_lines)
