/**
 * N-Queens AI Search - Frontend Application
 *
 * Provides:
 * - Dynamic SVG/HTML Chessboard rendering with coordinates and highlights
 * - Real-time search event consumption from Python backend (with offline JS fallback)
 * - Rock-solid playback controls: Start, Pause/Resume, Next Step, Reset
 * - Non-blocking speed slider adjusting consecutive step delays on the fly
 * - Educational step explanations, metrics, and redesigned clean event history
 */

// =============================================================================
// State Management
// =============================================================================

const state = {
  n: 4,
  algorithm: 'csp',
  events: [],
  stepIndex: 0,
  isPlaying: false,
  playbackTimeout: null,
  delayMs: 300,
  searchSearchSessionId: 0,
  currentStatus: 'Ready',
};

// DOM Element References
const elements = {
  nInput: document.getElementById('nInput'),
  algoSelect: document.getElementById('algoSelect'),
  startBtn: document.getElementById('startBtn'),
  stepBtn: document.getElementById('stepBtn'),
  resetBtn: document.getElementById('resetBtn'),
  speedSlider: document.getElementById('speedSlider'),
  speedValueLabel: document.getElementById('speedValueLabel'),
  statusBadge: document.getElementById('statusBadge'),
  boardTitle: document.getElementById('boardTitle'),
  stepCounter: document.getElementById('stepCounter'),
  chessboard: document.getElementById('chessboard'),
  stepExplanation: document.getElementById('stepExplanation'),
  m1Label: document.getElementById('m1Label'),
  m1Value: document.getElementById('m1Value'),
  m2Label: document.getElementById('m2Label'),
  m2Value: document.getElementById('m2Value'),
  m3Label: document.getElementById('m3Label'),
  m3Value: document.getElementById('m3Value'),
  m4Label: document.getElementById('m4Label'),
  m4Value: document.getElementById('m4Value'),
  detailsTitle: document.getElementById('detailsTitle'),
  detailsContent: document.getElementById('detailsContent'),
  logStream: document.getElementById('logStream'),
  clearLogBtn: document.getElementById('clearLogBtn'),
};

// =============================================================================
// Initialization & Event Listeners
// =============================================================================

function initApp() {
  // Speed slider input listener (triggers immediately on move)
  elements.speedSlider.addEventListener('input', (e) => {
    state.delayMs = parseInt(e.target.value, 10);
    const stepsPerSec = (1000 / state.delayMs).toFixed(1);
    elements.speedValueLabel.textContent = `${state.delayMs} ms (${stepsPerSec} steps/s)`;
  });

  // Algorithm selection listener
  elements.algoSelect.addEventListener('change', (e) => {
    state.algorithm = e.target.value;
    resetSearch();
  });

  // N input listener
  elements.nInput.addEventListener('change', (e) => {
    let val = parseInt(e.target.value, 10);
    if (isNaN(val) || val < 1) val = 1;
    if (val > 14) val = 14;
    elements.nInput.value = val;
    state.n = val;
    resetSearch();
  });

  // Control Buttons
  elements.startBtn.addEventListener('click', togglePlayPause);
  elements.stepBtn.addEventListener('click', stepForward);
  elements.resetBtn.addEventListener('click', resetSearch);
  elements.clearLogBtn.addEventListener('click', () => {
    elements.logStream.innerHTML = '';
  });

  // Initial empty board view
  renderEmptyBoard(state.n);
  updateMetricsLabels(state.algorithm);
  updateStatus('Ready');
}

// =============================================================================
// Board Rendering
// =============================================================================

function renderEmptyBoard(n) {
  elements.boardTitle.textContent = `Chessboard (N = ${n})`;
  elements.stepCounter.textContent = 'Step: 0 / 0';
  elements.chessboard.innerHTML = '';

  const maxWidth = Math.min(500, window.innerWidth - 60);
  const cellSize = Math.floor(maxWidth / n);
  elements.chessboard.style.setProperty('--cell-size', `${cellSize}px`);
  elements.chessboard.style.gridTemplateColumns = `repeat(${n}, ${cellSize}px)`;
  elements.chessboard.style.gridTemplateRows = `repeat(${n}, ${cellSize}px)`;

  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const cell = document.createElement('div');
      cell.className = `board-cell ${(r + c) % 2 === 0 ? 'tile-light' : 'tile-dark'}`;
      cell.dataset.row = r;
      cell.dataset.col = c;

      if (r === 0) {
        const colHeader = document.createElement('span');
        colHeader.className = 'coord-col-header';
        colHeader.textContent = c;
        cell.appendChild(colHeader);
      }
      if (c === 0) {
        const rowHeader = document.createElement('span');
        rowHeader.className = 'coord-row-header';
        rowHeader.textContent = r;
        cell.appendChild(rowHeader);
      }

      elements.chessboard.appendChild(cell);
    }
  }
}

function renderBoardState(event) {
  const n = state.n;
  const board = event.board;
  const highlight = event.highlight_cell;
  const status = event.cell_status;

  const cells = elements.chessboard.querySelectorAll('.board-cell');
  cells.forEach((cell) => {
    cell.classList.remove('hl-placed', 'hl-testing', 'hl-conflict', 'hl-backtrack', 'hl-moved', 'hl-expanded');
    const existingQueen = cell.querySelector('.queen-piece');
    if (existingQueen) cell.removeChild(existingQueen);
  });

  if (board && Array.isArray(board)) {
    board.forEach((r, c) => {
      if (r !== null && r !== undefined && r >= 0 && r < n && c < n) {
        const cell = elements.chessboard.querySelector(`[data-row="${r}"][data-col="${c}"]`);
        if (cell) {
          const queen = document.createElement('span');
          queen.className = 'queen-piece';
          queen.textContent = '♛';
          cell.appendChild(queen);
        }
      }
    });
  }

  if (highlight && Array.isArray(highlight) && highlight.length === 2) {
    const [hr, hc] = highlight;
    const targetCell = elements.chessboard.querySelector(`[data-row="${hr}"][data-col="${hc}"]`);
    if (targetCell) {
      if (status === 'placed') targetCell.classList.add('hl-placed');
      else if (status === 'testing') targetCell.classList.add('hl-testing');
      else if (status === 'conflict') targetCell.classList.add('hl-conflict');
      else if (status === 'backtrack') targetCell.classList.add('hl-backtrack');
      else if (status === 'moved') targetCell.classList.add('hl-moved');
      else if (status === 'expanded') targetCell.classList.add('hl-expanded');

      if (!targetCell.querySelector('.queen-piece') && ['testing', 'conflict', 'placed', 'moved'].includes(status)) {
        const queen = document.createElement('span');
        queen.className = 'queen-piece';
        queen.textContent = '♛';
        targetCell.appendChild(queen);
      }
    }
  }
}

// =============================================================================
// Status, Metrics & Explanation Updaters
// =============================================================================

function updateStatus(status) {
  state.currentStatus = status;
  elements.statusBadge.textContent = status;
  elements.statusBadge.className = 'status-badge';

  if (status === 'Ready') elements.statusBadge.classList.add('status-ready');
  else if (status === 'Searching') elements.statusBadge.classList.add('status-searching');
  else if (status === 'Paused') elements.statusBadge.classList.add('status-paused');
  else if (status === 'Solution Found') elements.statusBadge.classList.add('status-success');
  else if (status === 'No Solution') elements.statusBadge.classList.add('status-unsolvable');
  else if (status === 'Local Optimum') elements.statusBadge.classList.add('status-localopt');
  else if (status === 'Search Limit Reached') elements.statusBadge.classList.add('status-budget');
  else elements.statusBadge.classList.add('status-ready');
}

function updateMetricsLabels(algo) {
  if (algo.includes('hc') || algo.includes('hill')) {
    elements.m1Label.textContent = 'Conflicts h(n)';
    elements.m2Label.textContent = 'Gradient Steps';
    elements.m3Label.textContent = 'Random Restarts';
    elements.m4Label.textContent = 'H-Evaluations';
    elements.detailsTitle.textContent = 'Hill Climbing Strategy:';
    elements.detailsContent.textContent =
      algo === 'simple_hc'
        ? 'First-Choice: Accepts FIRST neighbor with h < current_h without evaluating others.'
        : 'Steepest-Ascent: Evaluates ALL N*(N-1) neighbors and picks the maximum drop.';
  } else if (algo === 'astar') {
    elements.m1Label.textContent = 'Depth / g(n)';
    elements.m2Label.textContent = 'Heuristic h(n)';
    elements.m3Label.textContent = 'Evaluation f(n) = g + h';
    elements.m4Label.textContent = 'Priority Queue Size';
    elements.detailsTitle.textContent = 'A* Frontier Details:';
    elements.detailsContent.textContent = 'Queue tracks partial non-attacking placements prioritized by f(n).';
  } else if (algo === 'csp') {
    elements.m1Label.textContent = 'Assignments';
    elements.m2Label.textContent = 'Backtracks';
    elements.m3Label.textContent = 'Constraint Checks';
    elements.m4Label.textContent = 'Unassigned Vars';
    elements.detailsTitle.textContent = 'Remaining Candidate Domains (MRV):';
    elements.detailsContent.textContent = 'Domains will update as Forward Checking prunes conflicts.';
  }
}

function updateMetricsValues(event) {
  const algo = state.algorithm;
  const m = event.metrics || {};

  if (algo.includes('hc') || algo.includes('hill')) {
    elements.m1Value.textContent = event.h !== null && event.h !== undefined ? event.h : (m.h ?? '-');
    elements.m2Value.textContent = m.steps ?? 0;
    elements.m3Value.textContent = m.restarts ?? 0;
    elements.m4Value.textContent = (m.heuristic_evaluations ?? 0).toLocaleString();
  } else if (algo === 'astar') {
    elements.m1Value.textContent = event.g !== null ? event.g : '-';
    elements.m2Value.textContent = event.h !== null ? event.h : '-';
    elements.m3Value.textContent = event.f !== null ? event.f : '-';
    elements.m4Value.textContent = event.frontier_size !== null ? event.frontier_size : (m.frontier_size ?? '-');

    const lines = [];
    if (event.current_state_tuple) lines.push(`Popped State: (${event.current_state_tuple.join(', ')})`);
    if (event.recent_children && event.recent_children.length > 0) {
      lines.push('Generated Safe Children:');
      event.recent_children.forEach((c) => lines.push(`  + ${c}`));
    }
    elements.detailsContent.textContent = lines.join('\n') || 'Expanding partial states...';
  } else if (algo === 'csp') {
    elements.m1Value.textContent = m.assignments ?? 0;
    elements.m2Value.textContent = m.backtracks ?? 0;
    elements.m3Value.textContent = (m.constraint_checks ?? 0).toLocaleString();

    const placedCount = (event.board || []).filter((x) => x !== null && x !== undefined).length;
    elements.m4Value.textContent = state.n - placedCount;

    if (event.domains) {
      const dLines = ['Remaining Candidate Rows per Column:'];
      for (const [col, rows] of Object.entries(event.domains)) {
        dLines.push(`  Col ${col} (X_${col}): [${rows.join(', ')}]`);
      }
      elements.detailsContent.textContent = dLines.join('\n');
    }
  }
}

function setExplanation(title, detail) {
  elements.stepExplanation.innerHTML = `
    <div class="explanation-title">${title}</div>
    <div class="explanation-detail">${detail}</div>
  `;
}

// Format concise 1-2 line explanation for the current step
function formatExplanation(event, algo) {
  const n = state.n;
  const m = event.metrics || {};
  const type = event.event_type;

  if (type === 'INIT') {
    return {
      title: 'Initial State',
      detail: `Random board generated with ${event.h} attacking pair${event.h === 1 ? '' : 's'}.`,
    };
  }

  if (type === 'MOVE') {
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    const newRow = event.highlight_cell ? event.highlight_cell[0] : (event.board ? event.board[col] : 0);
    const origRow = event.prevBoard && event.prevBoard[col] !== undefined ? event.prevBoard[col] : '?';
    const beforeH = event.prevH !== null ? event.prevH : '?';
    const afterH = event.h !== null ? event.h : (m.h ?? 0);

    if (algo === 'steepest_hc') {
      return {
        title: 'Best Neighbor Selected',
        detail: `Queen at C${col} moved R${origRow} → R${newRow}. Conflicts: ${beforeH} → ${afterH}.`,
      };
    } else {
      return {
        title: 'Move Accepted',
        detail: `Queen at C${col} moved R${origRow} → R${newRow}. Conflicts: ${beforeH} → ${afterH}.`,
      };
    }
  }

  if (type === 'LOCAL_MINIMUM' || type === 'PLATEAU') {
    return {
      title: 'Local Optimum',
      detail: `No move improves the current board (conflicts: ${event.h}).`,
    };
  }

  if (type === 'RESTART') {
    return {
      title: 'Random Restart',
      detail: `Starting with a new board.`,
    };
  }

  if (type === 'EXPAND') {
    const stateStr = event.current_state_tuple && event.current_state_tuple.length > 0
      ? `[${event.current_state_tuple.join(', ')}]`
      : '[]';
    const numChildren = event.recent_children ? event.recent_children.length : 0;
    return {
      title: 'State Expanded',
      detail: `Expanded ${stateStr}. Generated ${numChildren} valid child state${numChildren === 1 ? '' : 's'}.`,
    };
  }

  if (type === 'TEST_ASSIGNMENT') {
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    const row = event.highlight_cell ? event.highlight_cell[0] : 0;
    return {
      title: 'Testing Candidate',
      detail: `Evaluating Queen at C${col}, R${row}. Checking constraints...`,
    };
  }

  if (type === 'COMMIT_ASSIGNMENT') {
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    const row = event.highlight_cell ? event.highlight_cell[0] : 0;
    return {
      title: 'Assignment Committed',
      detail: `Assigned queen to C${col}, R${row}. Constraints satisfied.`,
    };
  }

  if (type === 'REJECT_ASSIGNMENT') {
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    const row = event.highlight_cell ? event.highlight_cell[0] : 0;
    return {
      title: 'Candidate Rejected',
      detail: `Rejected: C${col}, R${row} caused conflict or domain wipeout.`,
    };
  }

  if (type === 'BACKTRACK') {
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    return {
      title: 'Backtracking',
      detail: `Backtracking: C${col} has no valid remaining rows.`,
    };
  }

  if (type === 'GOAL') {
    return {
      title: 'Solution Found!',
      detail: `Solution found! All ${n} queens are non-attacking.`,
    };
  }

  if (type === 'NO_SOLUTION_EXISTS') {
    return {
      title: 'No Solution',
      detail: `Exhaustive search verified no solution exists for N = ${n}.`,
    };
  }

  if (type === 'BUDGET_EXHAUSTED') {
    return {
      title: 'Search Limit Reached',
      detail: `Search budget exhausted before reaching 0 conflicts.`,
    };
  }

  return {
    title: event.event_type,
    detail: event.description || '',
  };
}

// Format clean event card for the redesigned Event History
function formatEventCard(event, algo, stepIndex) {
  const type = event.event_type;
  const m = event.metrics || {};

  // Do not clutter event card history with purely internal variable selection events
  if (type === 'SELECT_VARIABLE') {
    return null;
  }

  let cardType = 'type-init';
  let title = '';
  let line1 = '';
  let line2 = '';

  if (type === 'INIT') {
    cardType = 'type-init';
    title = 'INITIAL STATE';
    line1 = `Random board generated · Conflicts: ${event.h}`;
  } else if (type === 'MOVE') {
    cardType = 'type-move';
    const stepNum = m.steps || stepIndex;
    title = `STEP ${stepNum} · MOVE ACCEPTED`;
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    const newRow = event.highlight_cell ? event.highlight_cell[0] : (event.board ? event.board[col] : 0);
    const origRow = event.prevBoard && event.prevBoard[col] !== undefined ? event.prevBoard[col] : '?';
    const beforeH = event.prevH !== null ? event.prevH : '?';
    const afterH = event.h !== null ? event.h : (m.h ?? 0);

    line1 = `Queen moved: Column ${col}, Row ${origRow} → Row ${newRow}`;
    line2 = `Conflicts: ${beforeH} → ${afterH}`;
  } else if (type === 'LOCAL_MINIMUM' || type === 'PLATEAU') {
    cardType = 'type-local-opt';
    title = 'LOCAL OPTIMUM';
    line1 = `No neighboring move reduces the current ${event.h} conflict${event.h === 1 ? '' : 's'}.`;
  } else if (type === 'RESTART') {
    cardType = 'type-restart';
    title = 'RANDOM RESTART';
    line1 = `New random board generated · Conflicts: ${event.h}`;
  } else if (type === 'EXPAND') {
    cardType = 'type-expand';
    const stepNum = m.expanded_nodes || stepIndex;
    title = `STEP ${stepNum} · STATE EXPANDED`;
    const stateStr = event.current_state_tuple && event.current_state_tuple.length > 0
      ? `[${event.current_state_tuple.join(', ')}]`
      : '[]';
    const numChildren = event.recent_children ? event.recent_children.length : 0;
    line1 = `Expanded ${stateStr} · Generated ${numChildren} safe child state${numChildren === 1 ? '' : 's'}`;
    line2 = `f(n) = ${event.f} (g=${event.g}, h=${event.h}) · Queue: ${event.frontier_size ?? '-'}`;
  } else if (type === 'TEST_ASSIGNMENT') {
    cardType = 'type-test';
    title = 'TESTING CANDIDATE';
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    const row = event.highlight_cell ? event.highlight_cell[0] : 0;
    line1 = `Testing Queen: Column ${col}, Row ${row}`;
    line2 = 'Checking constraints and forward checking...';
  } else if (type === 'COMMIT_ASSIGNMENT') {
    cardType = 'type-move';
    title = 'ASSIGNMENT COMMITTED';
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    const row = event.highlight_cell ? event.highlight_cell[0] : 0;
    line1 = `Assigned Queen: Column ${col}, Row ${row}`;
    line2 = 'Constraints satisfied · Forward checking passed';
  } else if (type === 'REJECT_ASSIGNMENT') {
    cardType = 'type-reject';
    title = 'CANDIDATE REJECTED';
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    const row = event.highlight_cell ? event.highlight_cell[0] : 0;
    line1 = `Rejected: Column ${col}, Row ${row}`;
    line2 = 'Caused row/diagonal clash or domain wipeout';
  } else if (type === 'BACKTRACK') {
    cardType = 'type-backtrack';
    title = 'BACKTRACKING';
    const col = event.highlight_cell ? event.highlight_cell[1] : 0;
    const row = event.highlight_cell ? event.highlight_cell[0] : 0;
    line1 = `Backtracked from: Column ${col}, Row ${row}`;
    line2 = 'No legal rows remaining · Domains restored';
  } else if (type === 'GOAL') {
    cardType = 'type-goal';
    title = 'SOLUTION FOUND';
    line1 = 'All queens are safe · Conflicts: 0';
  } else if (type === 'NO_SOLUTION_EXISTS') {
    cardType = 'type-fail';
    title = 'NO SOLUTION';
    line1 = `No non-attacking placement exists for N = ${state.n}`;
  } else if (type === 'BUDGET_EXHAUSTED' || type === 'FAILURE') {
    cardType = 'type-fail';
    title = 'SEARCH LIMIT REACHED';
    line1 = 'Search budget exhausted before reaching 0 conflicts';
  }

  const card = document.createElement('div');
  card.className = `event-card ${cardType}`;

  let html = `<div class="event-card-header"><span class="event-title">${title}</span></div>`;
  html += `<div class="event-desc">${line1}</div>`;
  if (line2) {
    html += `<div class="event-meta">${line2}</div>`;
  }
  card.innerHTML = html;
  return card;
}

// =============================================================================
// Search Execution & Playback Engine
// =============================================================================

async function fetchOrGenerateSearchEvents(algo, n) {
  try {
    const response = await fetch(`/api/search?algorithm=${encodeURIComponent(algo)}&n=${n}`);
    if (response.ok) {
      const data = await response.json();
      if (data.success && Array.isArray(data.events)) {
        return data.events;
      }
    }
  } catch (err) {
    console.warn('Backend /api/search unavailable, utilizing self-contained JS search engine:', err);
  }

  return runClientSideSearch(algo, n);
}

async function prepareSearch() {
  const sessionId = ++state.searchSearchSessionId;
  updateStatus('Searching');
  setExplanation('Preparing Search', 'Generating search event stream...');

  const events = await fetchOrGenerateSearchEvents(state.algorithm, state.n);

  if (sessionId !== state.searchSearchSessionId) return false;

  // Pre-annotate events with prior board and conflicts for exact before/after diffing
  let lastBoard = null;
  let lastH = null;
  for (let i = 0; i < events.length; i++) {
    const ev = events[i];
    ev.prevBoard = lastBoard ? [...lastBoard] : null;
    ev.prevH = lastH;
    if (ev.board && Array.isArray(ev.board)) {
      lastBoard = [...ev.board];
    }
    if (ev.h !== null && ev.h !== undefined) {
      lastH = ev.h;
    }
  }

  state.events = events;
  state.stepIndex = 0;
  elements.stepCounter.textContent = `Step: 0 / ${state.events.length}`;
  return true;
}

async function togglePlayPause() {
  if (state.isPlaying) {
    pauseSearch();
    return;
  }

  if (state.events.length > 0 && state.stepIndex < state.events.length) {
    resumeSearch();
    return;
  }

  const ready = await prepareSearch();
  if (ready) {
    resumeSearch();
  }
}

function resumeSearch() {
  if (state.stepIndex >= state.events.length) return;
  state.isPlaying = true;
  updateStatus('Searching');
  elements.startBtn.textContent = 'Pause ❚❚';
  elements.startBtn.classList.remove('btn-primary');
  elements.startBtn.classList.add('btn-secondary');
  elements.nInput.disabled = true;
  elements.algoSelect.disabled = true;

  scheduleNextPlaybackStep();
}

function pauseSearch() {
  state.isPlaying = false;
  if (state.playbackTimeout) {
    clearTimeout(state.playbackTimeout);
    state.playbackTimeout = null;
  }
  updateStatus('Paused');
  elements.startBtn.textContent = 'Resume ▶';
  elements.startBtn.classList.remove('btn-secondary');
  elements.startBtn.classList.add('btn-primary');
}

function scheduleNextPlaybackStep() {
  if (!state.isPlaying) return;

  state.playbackTimeout = setTimeout(() => {
    executeSingleStep();
    if (state.isPlaying && state.stepIndex < state.events.length) {
      scheduleNextPlaybackStep();
    } else if (state.stepIndex >= state.events.length) {
      state.isPlaying = false;
      elements.startBtn.textContent = 'Start ▶';
      elements.startBtn.classList.remove('btn-secondary');
      elements.startBtn.classList.add('btn-primary');
      elements.nInput.disabled = false;
      elements.algoSelect.disabled = false;
    }
  }, state.delayMs);
}

async function stepForward() {
  pauseSearch();

  if (state.events.length === 0 || state.stepIndex >= state.events.length) {
    const ready = await prepareSearch();
    if (!ready) return;
  }

  executeSingleStep();
}

function executeSingleStep() {
  if (state.stepIndex >= state.events.length) return;

  const event = state.events[state.stepIndex];
  state.stepIndex++;

  elements.stepCounter.textContent = `Step: ${state.stepIndex} / ${state.events.length}`;

  // Update concise explanation
  const expl = formatExplanation(event, state.algorithm);
  setExplanation(expl.title, expl.detail);

  // Render board & metrics
  renderBoardState(event);
  updateMetricsValues(event);

  // Append formatted event card to redesigned history
  const card = formatEventCard(event, state.algorithm, state.stepIndex);
  if (card) {
    elements.logStream.querySelectorAll('.event-card').forEach((c) => c.classList.remove('current'));
    card.classList.add('current');
    elements.logStream.appendChild(card);
    elements.logStream.scrollTop = elements.logStream.scrollHeight;
  }

  // Check if terminal
  if (event.is_terminal) {
    if (event.event_type === 'GOAL') updateStatus('Solution Found');
    else if (event.event_type === 'NO_SOLUTION_EXISTS') updateStatus('No Solution');
    else if (event.event_type === 'LOCAL_MINIMUM' || event.event_type === 'PLATEAU') updateStatus('Local Optimum');
    else if (event.event_type === 'BUDGET_EXHAUSTED') updateStatus('Search Limit Reached');
  }
}

function resetSearch() {
  state.searchSearchSessionId = (state.searchSearchSessionId || 0) + 1;
  pauseSearch();

  state.events = [];
  state.stepIndex = 0;

  elements.startBtn.textContent = 'Start ▶';
  elements.startBtn.classList.remove('btn-secondary');
  elements.startBtn.classList.add('btn-primary');
  elements.nInput.disabled = false;
  elements.algoSelect.disabled = false;

  renderEmptyBoard(state.n);
  updateMetricsLabels(state.algorithm);
  updateStatus('Ready');

  elements.m1Value.textContent = '-';
  elements.m2Value.textContent = '-';
  elements.m3Value.textContent = '-';
  elements.m4Value.textContent = '-';
  setExplanation('Ready to Start', 'Select an algorithm and board size N, then click <strong>Start</strong> or <strong>Next Step</strong>.');
  elements.logStream.innerHTML = `
    <div class="event-card type-init current">
      <div class="event-card-header"><span class="event-title">READY</span></div>
      <div class="event-desc">Select an algorithm and click Start or Next Step.</div>
    </div>
  `;
}

// =============================================================================
// Client-Side Algorithm Fallback (Offline / file:// protocol capability)
// =============================================================================

function countConflicts(board) {
  let conflicts = 0;
  const n = board.length;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (board[i] === board[j] || Math.abs(board[i] - board[j]) === Math.abs(i - j)) {
        conflicts++;
      }
    }
  }
  return conflicts;
}

function runClientSideSearch(algo, n) {
  if (algo === 'simple_hc') return runSimpleHC(n);
  if (algo === 'steepest_hc') return runSteepestHC(n);
  if (algo === 'astar') return runAStar(n);
  if (algo === 'csp') return runCSP(n);
  return [];
}

function runSimpleHC(n) {
  const events = [];
  let board = Array.from({ length: n }, () => Math.floor(Math.random() * n));
  let curH = countConflicts(board);
  let steps = 0;
  let restarts = 0;
  let evals = 1;

  events.push({
    event_type: 'INIT',
    board: [...board],
    description: `Simple HC Initial Board: h = ${curH} conflicts.`,
    metrics: { steps, restarts, heuristic_evaluations: evals, h: curH },
    h: curH,
  });

  if (curH === 0) {
    events.push({
      event_type: 'GOAL',
      board: [...board],
      description: 'Initial board is already a valid solution!',
      metrics: { steps, restarts, heuristic_evaluations: evals, h: 0 },
      highlight_cell: [board[0], 0],
      cell_status: 'placed',
      is_terminal: true,
    });
    return events;
  }

  for (let s = 1; s <= 200; s++) {
    steps++;
    let found = false;
    for (let col = 0; col < n; col++) {
      const orig = board[col];
      for (let r = 0; r < n; r++) {
        if (r === orig) continue;
        const neighbor = [...board];
        neighbor[col] = r;
        const h = countConflicts(neighbor);
        evals++;
        if (h < curH) {
          curH = h;
          board = neighbor;
          found = true;
          events.push({
            event_type: 'MOVE',
            board: [...board],
            description: `Simple HC Step ${steps}: Queen moved col ${col} (row ${orig} -> ${r}).`,
            highlight_cell: [r, col],
            cell_status: 'moved',
            metrics: { steps, restarts, heuristic_evaluations: evals, h: curH },
            h: curH,
          });
          if (curH === 0) {
            events.push({
              event_type: 'GOAL',
              board: [...board],
              description: `Solution Found with 0 conflicts at step ${steps}!`,
              highlight_cell: [r, col],
              cell_status: 'placed',
              metrics: { steps, restarts, heuristic_evaluations: evals, h: 0 },
              h: 0,
              is_terminal: true,
            });
            return events;
          }
          break;
        }
      }
      if (found) break;
    }
    if (!found) {
      events.push({
        event_type: 'LOCAL_MINIMUM',
        board: [...board],
        description: `Simple HC trapped in local optimum at step ${steps} (h = ${curH}).`,
        metrics: { steps, restarts: ++restarts, heuristic_evaluations: evals, h: curH },
        h: curH,
      });
      events.push({
        event_type: 'RESTART',
        board: [...board],
        description: `Random restart #${restarts}.`,
        metrics: { steps, restarts, heuristic_evaluations: evals, h: curH },
        h: curH,
      });
      board = Array.from({ length: n }, () => Math.floor(Math.random() * n));
      curH = countConflicts(board);
      evals++;
    }
  }
  events.push({ event_type: 'BUDGET_EXHAUSTED', board: [...board], description: 'Search budget limit reached.', is_terminal: true, metrics: { steps, restarts, heuristic_evaluations: evals } });
  return events;
}

function runSteepestHC(n) {
  const events = [];
  let board = Array.from({ length: n }, () => Math.floor(Math.random() * n));
  let curH = countConflicts(board);
  let steps = 0;
  let restarts = 0;
  let evals = 1;

  events.push({
    event_type: 'INIT',
    board: [...board],
    description: `Steepest HC Initial Board: h = ${curH} conflicts.`,
    metrics: { steps, restarts, heuristic_evaluations: evals, h: curH },
    h: curH,
  });

  if (curH === 0) {
    events.push({ event_type: 'GOAL', board: [...board], description: 'Initial state is a goal!', is_terminal: true, highlight_cell: [board[0], 0], cell_status: 'placed' });
    return events;
  }

  for (let s = 1; s <= 200; s++) {
    steps++;
    let bestH = curH;
    let bestNeighbor = null;
    let bestCol = -1;
    let bestRow = -1;

    for (let col = 0; col < n; col++) {
      const orig = board[col];
      for (let r = 0; r < n; r++) {
        if (r === orig) continue;
        const neighbor = [...board];
        neighbor[col] = r;
        const h = countConflicts(neighbor);
        evals++;
        if (h < bestH) {
          bestH = h;
          bestNeighbor = neighbor;
          bestCol = col;
          bestRow = r;
        }
      }
    }

    if (bestNeighbor) {
      curH = bestH;
      board = bestNeighbor;
      events.push({
        event_type: 'MOVE',
        board: [...board],
        description: `Steepest HC Step ${steps}: Best neighbor selected.`,
        highlight_cell: [bestRow, bestCol],
        cell_status: 'moved',
        metrics: { steps, restarts, heuristic_evaluations: evals, h: curH },
        h: curH,
      });
      if (curH === 0) {
        events.push({
          event_type: 'GOAL',
          board: [...board],
          description: `Steepest HC found solution at step ${steps}!`,
          highlight_cell: [bestRow, bestCol],
          cell_status: 'placed',
          metrics: { steps, restarts, heuristic_evaluations: evals, h: 0 },
          h: 0,
          is_terminal: true,
        });
        return events;
      }
    } else {
      events.push({
        event_type: 'LOCAL_MINIMUM',
        board: [...board],
        description: `Steepest HC trapped in local optimum at step ${steps}.`,
        metrics: { steps, restarts: ++restarts, heuristic_evaluations: evals, h: curH },
        h: curH,
      });
      events.push({
        event_type: 'RESTART',
        board: [...board],
        description: `Random restart #${restarts}.`,
        metrics: { steps, restarts, heuristic_evaluations: evals, h: curH },
        h: curH,
      });
      board = Array.from({ length: n }, () => Math.floor(Math.random() * n));
      curH = countConflicts(board);
      evals++;
    }
  }
  events.push({ event_type: 'BUDGET_EXHAUSTED', board: [...board], description: 'Search budget limit reached.', is_terminal: true, metrics: { steps, restarts, heuristic_evaluations: evals } });
  return events;
}

function runAStar(n) {
  const events = [];
  if (n === 2 || n === 3) {
    events.push({ event_type: 'NO_SOLUTION_EXISTS', board: null, description: `Mathematically no solution exists for N = ${n}.`, is_terminal: true });
    return events;
  }
  const queue = [{ state: [], g: 0, h: n, f: n }];
  let expanded = 0;
  let generated = 1;

  while (queue.length > 0 && generated < 20000) {
    queue.sort((a, b) => a.f - b.f || b.g - a.g);
    const curr = queue.shift();
    expanded++;
    const depth = curr.state.length;

    const board = Array.from({ length: n }, (_, c) => (c < depth ? curr.state[c] : null));

    if (depth === n) {
      events.push({
        event_type: 'GOAL',
        board: curr.state,
        description: `A* Goal Depth ${n} reached with f = ${curr.f}.`,
        highlight_cell: [curr.state[n - 1], n - 1],
        cell_status: 'placed',
        g: n,
        h: 0,
        f: curr.f,
        frontier_size: queue.length,
        metrics: { expanded_nodes: expanded, generated_nodes: generated, frontier_size: queue.length },
        is_terminal: true,
      });
      return events;
    }

    const nextCol = depth;
    const childrenDesc = [];
    for (let r = 0; r < n; r++) {
      let safe = true;
      for (let c = 0; c < depth; c++) {
        if (curr.state[c] === r || Math.abs(curr.state[c] - r) === Math.abs(c - nextCol)) {
          safe = false;
          break;
        }
      }
      if (safe) {
        const nextState = [...curr.state, r];
        const g = nextState.length;
        const h = n - g;
        const f = g + h;
        queue.push({ state: nextState, g, h, f });
        generated++;
        childrenDesc.push(`col ${nextCol}->row ${r} (f=${f})`);
      }
    }

    events.push({
      event_type: 'EXPAND',
      board,
      description: `A* popped state (${curr.state.join(', ')}). Depth=${depth}, f=${curr.f}.`,
      highlight_cell: depth > 0 ? [curr.state[depth - 1], depth - 1] : null,
      cell_status: 'expanded',
      g: curr.g,
      h: curr.h,
      f: curr.f,
      frontier_size: queue.length,
      current_state_tuple: curr.state,
      recent_children: childrenDesc,
      metrics: { expanded_nodes: expanded, generated_nodes: generated, frontier_size: queue.length },
    });
  }
  events.push({ event_type: 'NO_SOLUTION_EXISTS', board: null, description: 'Frontier exhausted with no solution.', is_terminal: true });
  return events;
}

function runCSP(n) {
  const events = [];
  if (n === 2 || n === 3) {
    events.push({ event_type: 'NO_SOLUTION_EXISTS', board: null, description: `Mathematically no solution exists for N = ${n}.`, is_terminal: true });
    return events;
  }

  const domains = {};
  for (let c = 0; c < n; c++) domains[c] = Array.from({ length: n }, (_, i) => i);
  const assignment = {};
  let assigns = 0;
  let backtracks = 0;
  let checks = 0;

  function selectMRV() {
    const unassigned = Object.keys(domains).filter((c) => !(c in assignment)).map(Number);
    unassigned.sort((a, b) => domains[a].length - domains[b].length || a - b);
    return unassigned[0];
  }

  function getBoard() {
    return Array.from({ length: n }, (_, c) => (c in assignment ? assignment[c] : null));
  }

  function solve() {
    if (Object.keys(assignment).length === n) return true;

    const varCol = selectMRV();
    const candidates = [...domains[varCol]];

    for (const r of candidates) {
      assigns++;
      assignment[varCol] = r;

      events.push({
        event_type: 'TEST_ASSIGNMENT',
        board: getBoard(),
        description: `Testing Queen at (row=${r}, col=${varCol}).`,
        highlight_cell: [r, varCol],
        cell_status: 'testing',
        domains: JSON.parse(JSON.stringify(domains)),
        metrics: { assignments: assigns, backtracks, constraint_checks: checks },
      });

      const pruned = {};
      let wipeout = false;
      for (let u = 0; u < n; u++) {
        if (u in assignment) continue;
        const colDist = Math.abs(u - varCol);
        const toPrune = [];
        for (const cv of domains[u]) {
          checks++;
          if (cv === r || Math.abs(cv - r) === colDist) {
            toPrune.push(cv);
          }
        }
        if (toPrune.length > 0) {
          pruned[u] = toPrune;
          domains[u] = domains[u].filter((v) => !toPrune.includes(v));
          if (domains[u].length === 0) {
            wipeout = true;
            break;
          }
        }
      }

      if (!wipeout) {
        events.push({
          event_type: 'COMMIT_ASSIGNMENT',
          board: getBoard(),
          description: `Committed assignment at (row=${r}, col=${varCol}).`,
          highlight_cell: [r, varCol],
          cell_status: 'placed',
          domains: JSON.parse(JSON.stringify(domains)),
          metrics: { assignments: assigns, backtracks, constraint_checks: checks },
        });

        if (solve()) return true;

        backtracks++;
        for (const [u, vals] of Object.entries(pruned)) {
          domains[u].push(...vals);
          domains[u].sort((a, b) => a - b);
        }
        delete assignment[varCol];

        events.push({
          event_type: 'BACKTRACK',
          board: getBoard(),
          description: `Backtracked from (row=${r}, col=${varCol}).`,
          highlight_cell: [r, varCol],
          cell_status: 'backtrack',
          domains: JSON.parse(JSON.stringify(domains)),
          metrics: { assignments: assigns, backtracks, constraint_checks: checks },
        });
      } else {
        backtracks++;
        for (const [u, vals] of Object.entries(pruned)) {
          domains[u].push(...vals);
          domains[u].sort((a, b) => a - b);
        }
        delete assignment[varCol];

        events.push({
          event_type: 'REJECT_ASSIGNMENT',
          board: getBoard(),
          description: `Rejected (row=${r}, col=${varCol}): Domain Wipeout!`,
          highlight_cell: [r, varCol],
          cell_status: 'conflict',
          domains: JSON.parse(JSON.stringify(domains)),
          metrics: { assignments: assigns, backtracks, constraint_checks: checks },
        });
      }
    }
    return false;
  }

  if (solve()) {
    const finalBoard = getBoard();
    events.push({
      event_type: 'GOAL',
      board: finalBoard,
      description: `CSP Solved! All ${n} queens safely assigned.`,
      highlight_cell: [finalBoard[n - 1], n - 1],
      cell_status: 'placed',
      metrics: { assignments: assigns, backtracks, constraint_checks: checks },
      is_terminal: true,
    });
  } else {
    events.push({
      event_type: 'NO_SOLUTION_EXISTS',
      board: null,
      description: 'CSP completed exhaustive search: no solution exists.',
      is_terminal: true,
      metrics: { assignments: assigns, backtracks, constraint_checks: checks },
    });
  }

  return events;
}

// Start application on page load
document.addEventListener('DOMContentLoaded', initApp);
