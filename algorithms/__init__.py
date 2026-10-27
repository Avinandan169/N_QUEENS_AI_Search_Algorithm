"""
Algorithms package for N-Queens solver.
"""

from algorithms.hill_climbing import (
    simple_hill_climbing_generator,
    solve_simple_hill_climbing,
    steepest_hill_climbing_generator,
    solve_steepest_hill_climbing,
    hill_climbing_generator,
    solve_hill_climbing,
)
from algorithms.astar import solve_astar, astar_generator
from algorithms.csp import solve_csp, csp_generator, CSPSolver

__all__ = [
    "simple_hill_climbing_generator",
    "solve_simple_hill_climbing",
    "steepest_hill_climbing_generator",
    "solve_steepest_hill_climbing",
    "hill_climbing_generator",
    "solve_hill_climbing",
    "solve_astar",
    "astar_generator",
    "solve_csp",
    "csp_generator",
    "CSPSolver",
]
