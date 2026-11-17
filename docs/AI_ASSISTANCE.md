# AI Assistance Log

Records material AI assistance: what was proposed, what was changed or rejected, and what was validated. Entries are dated. Only validation that was actually run is recorded as validated.

## 2026-11-17: Repository scaffolding

- **Tool:** Claude Code (Sonnet 5.5)
- **Proposed:** `.gitignore`, `.env.example`, `requirements.txt`, MIT `LICENSE`, `CONTRIBUTING.md`, this log, and the `src/` and `tests/` layout.
- **Changed or rejected:** The AI overwrote the existing GitHub-generated `.gitignore` and `LICENSE` without checking them first. Both were restored from git. The original `.gitignore` template was kept, with four lines added (`*.db`, `*.sqlite`, `*.sqlite3`, `data/generated/`). The original `LICENSE` was kept unchanged. _(add anything else from your review)_
- **Validated:** Nothing run yet. _(fill in, for example: `pip install -r requirements.txt` succeeds in a clean venv)_
- **Decisions made by me:** MIT license, `src/` layout.

## 2026-11-17: Synthetic data generator spec

- **Tool:** Claude Code (Sonnet 5.5)
- **Proposed:** Starting values and structure for `docs/synthetic-data-spec.md`: 40 items by 26 weeks, the weekday multiplier table, the per-item skew factor (k = 1.5, 1, 0), holiday lift and dip values, the four event types and multipliers, a note mix of about 20 events and 15 non-events, and the defect types. Also flagged that 4 to 6 day deliveries will not overlap lots for short-shelf-life items.
- **Changed or rejected:** Nothing rejected. I set the holiday lifts (40% and 50%), the delivery cadence (4 to 6 days), and the defect counts (3 to 5), and left the other federal holidays with no effect for now. I accepted the rest of the proposals.
- **Validated:** Nothing run. The spec is a design document. The values are starting points to tune against the backtest.
- **Decisions made by me:** the `holidays` package as the holiday source, CSV feed files as the output format, the four event types, and the item count and history length.
