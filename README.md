# N-Queens AI Search (Web Application)

A lightweight, interactive web application built for classroom projection and teaching students how Artificial Intelligence search algorithms work on the classic **N-Queens problem**.

Zero external runtime dependencies. Runs entirely using Python's standard library.

---

## Quick Start: Launch the Web Application

From the project root directory, run:

```bash
python3 server.py
```

The server will start and automatically open your default web browser to:
```
http://localhost:8000
```

*(You can also run `python3 main.py --web` or choose Option 6 in `python3 main.py`)*

---

## The Four Algorithms Implemented

| Algorithm | Strategy | Search Space | Key Characteristics |
| :--- | :--- | :--- | :--- |
| **1. Simple Hill Climbing** | First-Choice Greedy Local Search | Complete board ($N$ queens placed) | Scans neighbors in order; accepts the **FIRST** neighbor with fewer conflicts ($h < h_{\text{current}}$) and moves immediately. |
| **2. Steepest-Ascent Hill Climbing** | Best-Neighbor Local Search | Complete board ($N$ queens placed) | Evaluates **ALL** $N \times (N - 1)$ neighbors; selects the neighbor that achieves the maximum conflict reduction. |
| **3. A* Search** | Informed Tree Search | Partial board ($0 \le \text{depth} \le N$) | Places queens column by column. Priority queue orders states by $f(n) = g(n) + h(n)$ where $g(n) = \text{depth}$ and $h(n) = N - \text{depth}$. |
| **4. CSP Backtracking** | Constraint Satisfaction with MRV + Forward Checking | Variable assignments and domains | Employs Minimum Remaining Values (MRV) to pick the most constrained column and Forward Checking to prune conflicting candidate rows. |

---

## Interactive Teaching Controls

- **Board Size ($N$)**: Change board dimensions from $N = 1$ to $N = 12$ (default: $N = 4$).
- **Algorithm Selector**: Switch between Simple HC, Steepest-Ascent HC, A*, and CSP.
- **Start / Pause / Resume**: Starts continuous visualization. Click **Pause** to halt and discuss a step with students; click **Resume** to continue smoothly.
- **Next Step (⏭)**: Advances search by exactly **one discrete step**. Perfect for walking students through individual algorithm decisions.
- **Reset (↺)**: Cancels pending playback, clears the board, and resets metrics.
- **Dynamic Speed Slider (50 ms – 1500 ms)**:
  - Dragging the slider dynamically changes the playback rate for the **very next step** without restarting or resetting the search.
  - Displays real-time speed in milliseconds and steps per second (e.g., `300 ms (3.3 steps/s)`).

---

## Classroom Demonstration Guide

1. **Comparing Simple vs. Steepest-Ascent Hill Climbing**:
   - Set $N = 4$ or $N = 8$.
   - Select **Simple Hill Climbing** and click **Next Step**: show students how the algorithm accepts the *first* improving move it encounters without checking the rest of the board.
   - Select **Steepest-Ascent Hill Climbing** and click **Next Step**: show students how the algorithm evaluates all $N(N-1)$ neighbors to choose the steepest drop.
   - Point out how both detect **Local Optima** and trigger **Random Restarts**.

2. **Demonstrating A* Search**:
   - Select **A* Search** and set $N = 4$.
   - Click **Next Step**: observe how the search tree expands column by column.
   - Point to the metrics showing $g(n)$, $h(n)$, and $f(n) = 4$, and view the **Safe Children** generated in the frontier details box.

3. **Demonstrating CSP (MRV + Forward Checking)**:
   - Select **CSP Backtracking** and click **Next Step**:
   - Watch the yellow highlight for candidate testing.
   - Watch the green highlight when Forward Checking succeeds.
   - Watch the red flash on **Domain Wipeout** and purple on **Backtrack**, with the remaining candidate rows dynamically updated in the details box.

4. **Demonstrating Unsolvable Cases ($N = 2, 3$)**:
   - Set $N = 2$ or $N = 3$. Select A* or CSP and click **Start**.
   - The status immediately reflects `No Solution`, demonstrating how systematic search proves unsolvability.

---

## Command-Line Interface (CLI)

You can also run the terminal-based solver and comparison benchmarks:
```bash
python3 main.py
```

## Running Tests

Verify all four algorithms and event generators:
```bash
python3 -m unittest discover tests -v
```
