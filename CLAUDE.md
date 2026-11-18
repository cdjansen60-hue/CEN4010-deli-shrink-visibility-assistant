# CLAUDE.md

Project: **Deli Shrink Visibility Assistant** (CEN 4010 Final Project). Author: Caleb Jansen.
Repo: https://github.com/cdjansen60-hue/CEN1040-deli-shrink-visibility-assistant

## What this is

A decision-support prototype for grocery deli managers. It flags deli lots at risk of expiring unsold, ranked by days until expiration. The manager reviews every flag and keeps all ordering and rotation decisions. The system never orders, marks down, rotates, or discards anything, and markdown is never suggested.

## Source documents (read these first, in `docs/`)

- `CEN4010 - Assignment 2 - Solution Design Report Draft.md` is the authority for requirements (FR-1..FR-11, NFR-1..NFR-9), rules (Section 4.2), architecture (C1..C8, K1..K6, I1..I5), evidence (E1..E14), and build order (Section 8.1).
- `CEN4010 - Final Project.md` is the assignment: what must be delivered.
- `CEN4010 - Grading Criteria.md` is the rubric. Avoid excessive technical explanation typical of GenAI output.
- `CEN4010 - Guide to Canonical Architectures.md` covers the Data Intelligence pattern used here.

If code and the design report disagree, do not silently pick one. Flag it, and record the change (reason and effect) so the report can be updated. The report must distinguish planned from implemented.

## Decisions already made

- Language: Python. Forecast: scikit-learn `HistGradientBoostingRegressor` with quantile loss (10th, 50th, 90th percentiles), one global model, retrained weekly. A trailing same-weekday baseline always runs alongside it, and the baseline is used if the model loses the backtest (NFR-8).
- Data store: SQLite (relational, C2).
- Dashboard: Streamlit (C7). Streamlit enforces nothing, so review status, role checks, and the action log live in the Python/SQLite layer. The dashboard calls that layer and never writes to the database directly.
- Event interpreter (C3): Anthropic API when `ANTHROPIC_API_KEY` is set, otherwise a deterministic mock. The dashboard must show a visible "Mock interpreter" label when the mock is active. Only the note text and today's date are ever sent to the API (NFR-6).
- Data: synthetic only. Real store data is not authorized.
- Architecture: daily batch pipeline of eight components (C1 Ingestion and Validation, C2 Data Store, C3 Event Interpreter, C4 Forecast Service, C5 Lot Risk Engine, C6 Validation and Monitoring, C7 Review Dashboard, C8 Access Control and Audit). Components exchange records through C2.

## Key rules (details in report Section 4.2)

- Stock is tracked per lot (one delivery line = one lot). Sales are allocated oldest-expiration-first (FIFO). Discard scans carry no expiration date, so each discard is allocated to the oldest lot with stock, and discard validation is item-level only.
- Forecast horizon: days to the latest expiration among lots with stock, capped at 14. Needs at least 8 weeks of history. Under 4 weeks gives "insufficient history" and no forecast.
- Flag threshold: projected unsold of at least max(1 selling unit, 10% of lot received quantity).
- A missing sales day is never treated as zero. Missing expiration date, unmatched discards, and invalid rows go to the exception queue and are not assumed.
- Every estimate, forecast, and flag is labeled tier 2 (projected), distinct from tier 1 (observed).
- Only manager-confirmed events enter the forecast. The LLM never changes a number unreviewed.
- Employee identifiers in scan records are dropped at ingestion.

## Build order (report Section 8.1)

1. Synthetic data generator with documented injected effects (weekday, holiday, events, several lots per item, discards).
2. Data store, ingestion, exception queue (C1, C2).
3. Baseline forecast and lot risk engine (C5).
4. ML forecast and backtest (C4).
5. Context signals, event interpreter, confirmation gate (C3).
6. Dashboard review and action log (C7, C8).
7. Weekly calibration and pattern detection (C6).
8. Failure handling and performance.

Each step is done when its evidence items (E1..E14) pass. Write the test for an evidence item before or alongside the code that satisfies it.

## Working rules

- Treat generated code as a candidate. Run it and review it. Do not claim a validation result that has not been run.
- Keep AI assistance logged in `docs/AI_ASSISTANCE.md` (what was proposed, what was changed or rejected, what was validated).
- Make small commits with meaningful messages, one logical change each.
- Never commit secrets. Keep `.env` gitignored and ship `.env.example` with blank values. Tests must not call the real API; use the mock.
- Keep thresholds and windows configurable in one config file, since they are starting values to tune against the backtest.
- Keep the scope bounded. No ordering, POS, or pricing integration, no real-time processing, no theft-driven shrink.

## Repository expectations (Final Project deliverable)

README.md (purpose, architecture summary, prerequisites, setup, configuration, run and test instructions, sample data guidance, limitations, repo link), LICENSE, CONTRIBUTING.md, tests, config, and docs. A reviewer must be able to stand up and run the project from the repo, with and without an API key.

## Commands (fill in as they are created)

- Setup: `pip install -r requirements.txt`
- Generate data: `python -m src.generate_data --items 40 --weeks 26 --seed 42 --out data/generated` (writes feeds plus a `truth/` folder the pipeline must never read; `data/generated/` is gitignored)
- Run pipeline: TBD
- Run dashboard: `streamlit run app.py` (TBD)
- Tests: `pytest`
