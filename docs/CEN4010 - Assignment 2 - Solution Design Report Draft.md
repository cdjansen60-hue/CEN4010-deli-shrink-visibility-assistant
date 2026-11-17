CEN 4010 · Principles of Software Engineering · Assignment 2

# Solution Design Report

**Project title** · Deli Shrink Visibility Assistant
**Author** · Caleb Jansen (cjansen2026@fau.edu)

> Report for [`Assignment 2`](./CEN4010%20-%20Assignment%202.md). Sections 1 to 5 reuse and revise the Assignment 1 baseline ([`Baseline v2`](./CEN4010%20-%20Assignment%201%20-%20Solution%20Design%20Report%20Baseline%20v2.md)); Sections 6 to 8 are new. Every change is recorded in Appendix B. Proof of Demand is omitted.

---

## 1. Executive Summary

The deli department of a grocery store sells almost nothing with a long shelf life, yet physical inventory counts there happen only quarterly. Spoiled and expired product is scanned and logged daily as it is discarded, but that log is never analyzed, and nothing projects which items will spoil next. The deli manager, who also places the next order, therefore decides on a picture of shrink that can be up to a quarter old, often without knowing about a current event that will change demand.

I arrived at this problem from my own grocery-store work experience and from a conversation with a family member who currently works in a grocery deli. Section 2.1 records what I learned and how it changed the design.

The proposed solution is a decision-support tool, not an automated one. From data the deli already produces (receiving by lot, daily sales, and the discard log) plus outside signals such as holidays, weather, and manager-confirmed local events, it forecasts demand for each item with a machine-learning model, projects how much of each lot will be unsold at its expiration date, and flags the lots at risk, ranked by days until expiration. The manager reviews every flag and keeps every ordering and rotation decision. Markdown is not routine practice in this deli, so the manager's levers are the next order and rotation.

This report extends Assignment 1 by revising its baseline in response to the grading feedback (Sections 1 to 5, with changes logged in Appendix B) and by adding a solution architecture, solution design, and implementation guidelines (Sections 6 to 8). The architecture is a daily batch pipeline of eight components built on the Data Intelligence pattern from the course guide, with one runtime GenAI component whose output the manager must confirm. The scope is a focused prototype: it excludes theft-driven shrink, ordering or POS integration, real-time processing, and real store data. For the Final Project, Section 8 sets the build order, the evidence the prototype must produce, and the boundaries on AI-assisted development.

## 2. Problem Scenario

### 2.1 Who Cares, and What Discovery Showed

**Who cares.** Deli department managers at grocery stores. They own shrink for their department, place the orders that drive it, and are measured on it, yet they learn the full scale of the loss only at the quarterly count.

**Who I spoke with.** A family member currently working in a grocery deli, plus my own experience working in a grocery store.

**What I learned, and what it changed:**

| Finding | Effect on the design |
|---|---|
| Fresh departments are counted quarterly, grocery (dry goods) yearly. Fresh shrink comes mainly from short shelf life, grocery shrink mainly from theft. | Scoped to the deli. Theft excluded as a separate problem. |
| Every discard is scanned daily with a scan gun into a spreadsheet or database. | The discard log is an existing data source, not a gap. It became an input for calibration and pattern detection (FR-10). |
| Markdown does not happen in the deli except in extreme cases, such as a clerical ordering mistake. | The manager's levers are the next order and rotation. Markdown is exception-only and the system never suggests it. |
| FIFO rotation is policy, but how well it is followed depends on the worker. | Per-lot stock is an estimate that assumes FIFO. Rotation lapses are recorded as a limitation (2.10). |
| A manager would find a list ranked by days until expiration most useful. | Flags are ranked by days until expiration (FR-6). |
| Receiving records carry an expiration date per delivery line, so one item can hold several lots. | The model tracks stock per lot, not per item (FR-1, FR-5). |
| From my own time working in a grocery store: much of the shrink I saw came after a manager ordered a normal amount, or more, without knowing about a current event that drew sales away. | Outside signals are inputs, and a forecasting model is used, so an event the manager confirms changes the forecast before the order is placed (FR-3, FR-4). |

### 2.2 Operating Context and Current Workflow

The deli manager owns shrink for the department day to day. Product is received against a purchase order and stocked in the case. Clerks rotate stock and pull spoiled or expired items, scanning each one into the discard log. The only point where shrink is reconciled against book inventory is the quarterly physical count, so between counts the log accumulates without anyone aggregating it. Figure 1 (Section 3) shows this cycle.

- **Deli manager**: provides receiving and sales information, reviews flagged items, corrects records, and owns ordering and rotation decisions.
- **Deli clerks**: record discards and act on rotation and stocking; they do not make ordering decisions.
- **Store manager**: reviews aggregate shrink at the quarterly count and makes escalated or store-wide decisions.

### 2.3 Loss Triggers

| # | Trigger | Condition |
|---|---|---|
| T1 | Approaching expiration with slow sell-through | A lot's expiration date is close and its remaining quantity is high relative to expected sales. |
| T2 | Over-ordering relative to demand | The next order is placed from a standing level or recent memory of demand, often without knowledge of a current event that will pull sales away, so more arrives than can sell before spoilage. |
| T3 | Delayed discovery of the pattern | Because reconciliation is quarterly, a recurring problem is not visible until the quarter closes, even though the discards were logged daily. |
| T4 | Inconsistent rotation | FIFO is policy but depends on the worker, so older stock can age out while newer stock sells. |

### 2.4 Bounded Problem Statement

**In scope.** Between quarterly counts, the deli manager cannot see which lots are on track to spoil before they sell, or whether a recurring pattern is driving it, even though the data that could show it already exists. Corrective action (adjusting the next order or tightening rotation) therefore comes too late.

**Out of scope.** Final order quantities, vendor terms, staffing, and markdown policy remain management decisions. Theft-driven shrink in dry-goods departments is excluded.

### 2.5 Desired Improvement

| Goal | Statement |
|---|---|
| G1 | The manager sees, continuously rather than quarterly, which lots are at risk of spoiling before they sell. |
| G2 | At-risk lots are ranked by how soon they expire. |
| G3 | Every flag shows the data and assumptions that produced it. |
| G4 | Recurring shrink patterns become visible across weeks. |
| G5 | The manager keeps every ordering and rotation decision, and markdown stays exception-only. |
| G6 | The forecast reflects conditions beyond recent sales, such as holidays, weather, and local events. |

### 2.6 Data Sources and Availability

| Source | Fields needed | Format | Status |
|---|---|---|---|
| Lot receiving | SKU, delivery line, quantity, receipt date, expiration date | Invoices recorded in the store's SIIMS program; export format unknown | Per-line expiration confirmed in general terms. Field-level export format unconfirmed. |
| Sales | SKU, date, quantity sold | POS export by SKU and day | Assumed available at SKU-day level. Not yet checked field by field. |
| Discard log | SKU, quantity, date and time | Scan-gun entries in a spreadsheet or database | Daily capture confirmed. The scan does not record an expiration date, as far as my family member can tell. |
| Context signals | Holidays, weather forecast, local events | Public calendars and weather forecasts, plus manager-entered notes | Public sources; manager notes are new manual input. |
| Prototype data | All of the above | Synthetic, generated to match the patterns above | Real store data is not authorized for student use. |

I could find no public documentation of SIIMS, so its export fields cannot be verified from outside sources. The design therefore uses a generic file contract (I1) with one thin adapter per source, so a different export layout changes only the adapter. Before the Final Project, I will ask the deli employee for a sample export to confirm field names.

### 2.7 Why a Forecasting Model, and Alternatives Considered

**What stays conventional.** Days until expiration, per-lot stock estimates, ranking, and discard matching are plain arithmetic and rules, and nothing about them needs AI.

**What a model is for.** The one hard problem is predicting demand when it depends on factors recent sales do not capture: weekday patterns, holidays, weather, and local events. A trailing average cannot use those signals, so it will misjudge a weekend with a home game or a holiday. A trained forecast can. One-time events have no history to learn from, so the manager confirms them as inputs and the model learns how to use them from comparable past events.

| Alternative | What it would do | Why it was not chosen |
|---|---|---|
| More frequent physical counts | Shorten the gap between counts | Adds labor and still measures loss after it happens. |
| Weekly discard-totals report | Summarize the existing log | Cheap and useful, so it is kept as FR-10, but it is retrospective and cannot warn before spoilage. |
| Off-the-shelf replenishment module | Optimize and place orders automatically | Removes the manager's authority and assumes ordering integration beyond this scope. |
| Auto-markdown or price optimization | Discount items near expiration | Assumes a practice this deli does not use. |
| Trailing-average forecast | Predict demand from recent sales only | Simple and explainable but blind to outside signals. Kept as the comparison baseline (NFR-8). |
| Manager spreadsheet and judgment | Status quo | Depends on one person's memory and does not scale across lots. |

The design follows the Data Intelligence pattern in the course guide: ingestion, a data store, a model service, a recommendation step, and a validation and monitoring workbench. Section 7 maps the components to that pattern.

### 2.8 Representative Scenarios

| # | Scenario | Expected behavior | Requirements |
|---|---|---|---|
| S1 | Sliced turkey lot of 12 lb expires in 5 days. Forecast demand is 1.6 lb per day. | Projected unsold is 4 lb, above the threshold, so the lot is flagged with its basis shown. | FR-4, 5, 7 |
| S2 | Two lots of one item: lot A, 6 lb, expires in 2 days; lot B, 8 lb, expires in 6. Demand is 2 lb per day. | Sales are allocated to A first. A is flagged with 2 lb unsold. B is not flagged. A ranks first. | FR-1, 5, 6 |
| S3 | A lot of 9 lb expires Sunday and is flagged at 1 lb unsold. The manager enters "high school playoff game Friday night." | The note becomes an event candidate and is not used until confirmed. Once confirmed, Friday demand rises, the projection falls to 0 lb, and the flag clears. The history shows the event as the reason. | FR-3, 4, 7 |
| S4 | The sales file for one item is missing for two days. | Missing days are not treated as zero. The item shows a data gap, new flags for it are suppressed, and an exception is raised. | FR-2, 11 |
| S5 | At week's end S1's flag projected 4 lb unsold, and the discard log shows 5 lb discarded. | The calibration report shows a 1 lb variance at item level. It does not claim lot-level confirmation because the scan did not record an expiration date. | FR-10 |
| S6 | The manager reviews a flag and reduces next week's order outside the system. | The system records the review and the action. It places no order. | FR-9 |

### 2.9 Evidence Status, Constraints, and Risks

| Tier | Kind of statement | Standing |
|---|---|---|
| 1 | Observed: received quantity, expiration date, recorded sales, logged discards | Confirmed; what the system actually knows. |
| 2 | Derived or projected: estimated lot stock, demand forecast, risk flag | A prediction or estimate, always shown as one and never as a foregone loss. |

**Constraints.** Prediction is always labeled as prediction, the system never acts on its own, ordering and rotation stay with management, and development uses synthetic data because real store data is not authorized.

| # | Risk | Why it matters |
|---|---|---|
| R1 | False confidence in a prediction | An inaccurate flag could drive a bad ordering decision if the manager stops checking. |
| R2 | Alert fatigue | Too many or poorly ranked flags would lead the manager to ignore the tool. |
| R3 | Data gaps | Missing or inconsistent receiving, sales, or discard data makes flags unreliable. |
| R4 | Scope creep into ordering or markdown | A flagging tool could be asked to place orders or mark down, removing decisions that belong to the manager. |

### 2.10 Limitations

- **Synthetic data limits what testing proves.** A model tested on data I generate shows the pipeline works, not that it will forecast a real deli. Real-data validation falls outside this course.
- **One-time events need a human input.** The model cannot predict an event it has no history of, so it depends on the manager entering and confirming events.
- **Per-lot stock is an estimate.** Sales are recorded per item, not per lot, so allocation assumes FIFO, which depends on the worker.
- **Rotation lapses (T4) are not directly detectable** from receiving, sales, and discard data as described.
- **Discard records confirm outcomes at item level only.** The scan carries no expiration date, so a discard cannot be tied to a specific lot, and each discard is allocated to the oldest lot with stock.
- **No measured baseline exists** for current shrink, so improvement is judged against the trailing-average forecast, not against today's loss.
- **Field-level formats are unconfirmed** (2.6).

## 3. Scenario Reference Diagram

![Figure 1: Current deli shrink workflow, receiving to next order](./CEN4010%20-%20Assignment%201%20-%20Figure%201%20%28scenario%20diagram%29.png)

**Figure 1.** The current workflow still explains the work and is reused unchanged. The discard log at stage 2 already holds item-level evidence of where loss happens, but nothing reads it until the count at stage 5. The proposed capability reads receiving, sales, the discard log, and context signals so the manager can act during stage 2.

## 4. Functional Requirements and Validation Questions

Definitions used by these requirements are in 4.2.

| Requirement ID | Functional Requirement | Validation Question | Expected Evidence or Test Result |
|---|---|---|---|
| FR-1 | The system shall record each delivery line as a separate lot with its item, quantity, receipt date, and expiration date. | When a test delivery has two lines for one item with different expiration dates, does the system store two lots? | Two lots exist, each with its own quantity, receipt date, and expiration date. |
| FR-2 | The system shall ingest daily sales per item and detect missing days. | When a day's sales are missing for an item, does the system record a gap rather than zero sales? | A data gap is recorded for that item and day, and no zero is stored. |
| FR-3 | The system shall ingest holidays, weather forecasts, and manager event notes, and shall turn each manager note into a structured event candidate that the forecast uses only after the manager confirms it. If the interpreter returns invalid output, the system shall retry once, then raise an exception and ask the manager to rewrite the note. | When a manager note is submitted, does the system produce a candidate and withhold it from the forecast until confirmed, and does an invalid interpreter output produce an exception instead of a candidate? | A candidate with event type and date appears, and the forecast is unchanged until the manager confirms it. An invalid output becomes an exception and creates no candidate. |
| FR-4 | The system shall forecast daily demand per item over the forecast horizon, with an 80% prediction interval, from sales history and confirmed context signals. If the forecast model is unavailable, the system shall use the trailing-average baseline and label every dependent flag. | For an item whose synthetic history contains a holiday uplift, does the forecast for the holiday date reflect it and show an interval, and with the model disabled are flags still produced and labeled? | The holiday forecast exceeds the same-weekday baseline by the injected uplift within an agreed tolerance, and an interval is shown. With the model disabled, flags come from the baseline and are labeled as baseline forecasts. |
| FR-5 | The system shall estimate stock per lot, project the unsold quantity at each lot's expiration date, and flag each lot at or above the flag threshold. | For an item with two lots and known demand, do the projected unsold quantities and flags match a hand calculation? | Projected quantities and flags match the hand calculation for every lot. |
| FR-6 | The system shall rank flags by days until expiration, soonest first, breaking ties by projected unsold quantity. | For a set of flags with known expiration dates and quantities, does the order match a hand-sorted order? | The system order matches the hand-sorted order. |
| FR-7 | Each flag shall show its basis: the lot record, the forecast with its interval, the context signals used, and the stock-allocation assumption. | For a sample flag, can a reviewer reach each of these four items? | All four resolve to specific records with values matching the flag. |
| FR-8 | The system shall label every estimate, forecast, and flag as tier 2, visibly distinct from tier-1 data. | Does a sample report show for each statement whether it is observed or projected? | Every tier-2 statement is labeled, and none appears with tier-1 standing. |
| FR-9 | The system shall let the manager mark a flag reviewed, dismiss it with a reason, and record any action taken, without performing the action. | Can a manager review, dismiss, and log an action, and does the system take none of those actions itself? | Status, reason, and action are stored, and no order, rotation, discard, or markdown is executed. |
| FR-10 | The system shall ingest the discard log and report, weekly per item, the projected unsold quantity against the quantity discarded, and shall surface items discarded in three or more consecutive weeks. | For an item flagged last week, does the weekly report show projected against actual, and does a three-week pattern surface? | The report shows both quantities and the variance, and a three-week item appears as a recurring pattern. |
| FR-11 | The system shall route missing, invalid, or conflicting data to an exception queue instead of assuming a value. | When a lot arrives with no expiration date, is it excluded from flagging and listed in the queue? | The lot is absent from flags and present in the queue with the reason. |

### 4.1 Priorities and Traceability

Priority uses MoSCoW for the Final Project prototype. Each requirement traces to a goal from 2.5 and to the scenarios in 2.8.

| Requirement | Priority | Goal | Scenario | Rationale |
|---|---|---|---|---|
| FR-1 | Must | G1 | S2 | Lot-level tracking is needed because items hold several expiration dates. |
| FR-2 | Must | G1, G6 | S4 | The forecast depends on complete sales history. |
| FR-3 | Must | G6 | S3 | Outside signals are the reason a model is used. |
| FR-4 | Must | G1, G6 | S1, S3 | The forecast is the core capability. |
| FR-5 | Must | G1 | S1, S2 | This produces the flags. |
| FR-6 | Must | G2 | S2 | The manager asked for ranking by days until expiration. |
| FR-7 | Must | G3 | S1, S3 | The manager must be able to judge a flag. |
| FR-8 | Must | G3, G5 | all | Prevents false confidence (R1). |
| FR-9 | Must | G5 | S6 | Keeps human authority. |
| FR-10 | Should | G4 | S5 | Delivers pattern visibility and calibration, but the flags work without it. |
| FR-11 | Must | G3 | S4 | Prevents silent assumptions (R3). |

### 4.2 Calculation and Data-Handling Rules

Initial values are starting points to tune against the prototype backtest.

| Rule | Definition |
|---|---|
| Estimated lot stock | Received quantity, minus sales allocated oldest-expiration-first (assumes FIFO), minus discards. Discard scans carry no expiration date, so each discard is allocated to the oldest lot with stock. |
| Forecast horizon | Days from today to the latest expiration date among lots with stock, capped at 14 days. |
| Training window | At least 8 weeks of daily sales, retrained weekly. An item with fewer than 4 weeks of history gets no forecast and shows "insufficient history." |
| Projected unsold | For each lot, estimated stock minus forecast demand consumed from that lot before it expires, taking lots in expiration order. |
| Flag threshold | Projected unsold of at least the larger of 1 selling unit or 10% of the lot's received quantity. |
| Missing sales | A missing day is never zero. One missing day carries the forecast forward with a data-gap label. Two or more consecutive days suppress new flags for that item and raise an exception. |
| Missing expiration date | The lot is excluded from flagging and listed in the exception queue. |
| Unmatched discard | A discard that matches no item goes to the exception queue and is not counted. |
| Context unavailable | The forecast runs without it, and flags are labeled "context signals unavailable." |
| Discard validation | Weekly, per item: projected unsold against discarded quantity. No lot-level confirmation is claimed, because discard scans carry no expiration date. |

## 5. Non-Functional Requirements

| Requirement ID | Category | Measurable Requirement |
|---|---|---|
| NFR-1 | Timeliness | The daily refresh shall finish within 30 minutes of the day's data becoming available, for up to 500 items. |
| NFR-2 | Readability | Flags shall appear in one list sorted by days until expiration, each with a reason of at most two sentences, and up to 25 flags shall fit on one screen. |
| NFR-3 | Source Traceability | The system shall keep each at-risk flag's links to its lot, forecast, context signals, and allocation assumption, and each recurring-pattern flag's links to its discard-log entries, for at least the current quarterly cycle. |
| NFR-4 | Privacy / Security | Access shall be limited to authenticated staff and managers assigned to the store and department, and employee identifiers in scan records shall be dropped at ingestion and shall not appear in forecasts or reports. |
| NFR-5 | Retained Human Authority | The system shall not execute an order, rotation, discard, or markdown, and markdown shall never be suggested. |
| NFR-6 | AI-Assisted Operating Context | Every model output and event interpretation shall be a tier-2 candidate, only manager-confirmed events shall enter the forecast, each run shall record the model version, training window, and inputs, and only event-note text shall be sent to an external model. |
| NFR-7 | Reliability | When a daily run fails, the system shall show the last successful results with a banner stating their age, and shall not present stale results as current. |
| NFR-8 | Forecast Quality | On a held-out synthetic backtest, the forecast's mean absolute error shall be no higher than the trailing same-weekday baseline's, reported side by side. If it is higher, the baseline shall be used. |
| NFR-9 | Review Status | Every flag shall display its current status (open, reviewed, dismissed, or expired) and, once reviewed or dismissed, who changed it and when. |

| Requirement | Priority | Goal |
|---|---|---|
| NFR-1, 2, 3, 5, 6, 8, 9 | Must | G1, G3, G5, G6 |
| NFR-4, 7 | Should | G3, G5 |

## 6. Solution Architecture Diagram

![Figure 2: Solution architecture](./CEN4010%20-%20Assignment%202%20-%20Figure%202%20%28architecture%20diagram%29.png)

**Figure 2. Solution architecture of the Deli Shrink Visibility Assistant.** Dashed boxes are external dependencies, purple components use AI, and the green components are where the manager reviews and decides. Arrows show information moving; the system has no arrow to any ordering, pricing, or POS system. Control points K1 to K6 are listed after the figure.

| Point | Control | Requirements |
|---|---|---|
| K1 | Schema and completeness checks on every incoming file | FR-2, FR-11 |
| K2 | Event confirmation gate: an unconfirmed event never reaches the forecast | FR-3, NFR-6 |
| K3 | Tier-2 labeling on every forecast and flag | FR-8 |
| K4 | Flag threshold, and no connection from the system to any action | FR-5, NFR-5 |
| K5 | Manager review, override, and action log | FR-9 |
| K6 | Run log, monitoring, and stale-run banner | FR-10, NFR-7 |

## 7. Solution Design

### 7.1 Explanation of the Solution Architecture

The architecture follows the Data Intelligence pattern in the course guide: ingestion, a data store, AI model services, a recommendation step, and a validation and monitoring workbench. It replaces the quarterly, retrospective review in Figure 1 with a daily loop in which the deli's own data produces ranked, explained flags for the manager to act on during stage 2 of the workflow. Section 8.4 maps every goal and requirement to the components and controls that support it.

**Architecture alternatives considered.** I used GenAI to propose these and decided among them.

| Alternative | Why not chosen |
|---|---|
| A. One script writing a spreadsheet | Fastest to build, but it cannot enforce the review gate, keep traceability, or log actions. |
| B. Batch pipeline with a data store and review dashboard | **Chosen.** Matches daily data, separates each responsibility, and puts controls at each boundary. |
| C. Real-time streaming | Receiving and sales data arrive daily and NFR-1 needs only a daily refresh, so streaming adds infrastructure without benefit. |
| D. An LLM agent that reads the data and writes recommendations | Unreliable at arithmetic, hard to trace, and it would blur the line between suggestion and decision. |

**Component design decisions.**

| Decision | Choice | Alternatives and reason |
|---|---|---|
| Forecast model | One global gradient-boosted regression with quantile loss (10th, 50th, 90th percentiles), retrained weekly | Per-item classical models have too little history per item. Deep sequence models need more data and explain less. Quantile output gives the 80% interval directly. |
| Data store | Relational database | Records are structured and linked, and flags need to join lots, forecasts, and events. |
| Event interpretation | LLM with a strict output schema and a confirmation gate | A structured form is more predictable but removes free-text input. The gate keeps the LLM from affecting any number unreviewed. |
| Interface | Web dashboard | A spreadsheet cannot enforce review status or action logging. |

### 7.2 Components

| ID | Responsibility | Inputs | Outputs | Dependencies and interfaces |
|---|---|---|---|---|
| C1 Ingestion and Validation | Load daily files, validate, drop employee identifiers, route problems to exceptions | Receiving, sales, discard files; weather and holiday feeds | Validated records, exceptions | External sources (I1), writes to C2 |
| C2 Data Store | Hold all records and the history linking them | Records from C1, C3, C4, C5, C6, C7 | Records to every component | None; all components use it |
| C3 Event Interpreter (GenAI) | Convert a manager's note into a structured event candidate | Note text | Candidate with status "proposed" | LLM provider (I2), C2 |
| C4 Forecast Service (ML) | Forecast daily demand with an interval; run the baseline alongside | Sales history, context signals, confirmed events | Forecasts with model version | C2 (I3) |
| C5 Lot Risk Engine | Estimate lot stock, project unsold, flag, rank | Lots, forecasts, thresholds | Flags with basis references | C2 (I4) |
| C6 Validation and Monitoring | Weekly calibration, backtest against baseline, pattern detection, run monitoring | Forecasts, flags, discards, run log | Calibration reports, patterns, model comparison | C2 |
| C7 Review Dashboard | Show flags and their basis; take notes, confirmations, reviews, and actions | Flags, candidates, exceptions, reports | Notes, confirmations, review records | C2 (I5), C8 |
| C8 Access Control and Audit | Authenticate users, enforce roles, record every review, confirmation, and run | User actions, run events | Allow or deny, audit records | All components |

Allowed interactions: components exchange records through C2. The arrows into C7 in Figure 2 show what the dashboard displays, which it reads from C2 through I5, and C4 passes forecasts to C5 within a run. Only C3 may send data to the LLM provider, and only note text.

### 7.3 Component Behavior, Information, and Interfaces

**Information structures** (all records also carry a source file or run reference):

| Entity | Key fields |
|---|---|
| lot | lot ID, item, delivery line, received quantity, unit, receipt date, expiration date |
| sales_daily | item, date, quantity sold |
| discard | item, quantity, unit, discarded at; employee identifier is not kept |
| context_signal | date, type (holiday or weather), value, source |
| event_candidate | note text, proposed type, start and end date, direction, magnitude, rationale, status (proposed, confirmed, edited, rejected), decided by and at, interpreter version |
| forecast | run, item, date, 10th, 50th, and 90th percentile demand, baseline demand, model version |
| flag | run, lot, days to expiration, estimated stock, projected unsold (low, point, high), threshold, rank, status (open, reviewed, dismissed, expired), tier 2, references to forecast, events, and allocation assumption |
| review | flag, reviewer, decision, reason, action taken, time |
| exception | type, record reference, reason, status |
| run_log | run, stage statuses, times, model version, record counts |

**Interface contracts:**

| Interface | Contract |
|---|---|
| I1 Source files | One generic CSV file per source per day with required columns and types as in the entity table; an adapter per source maps the store's own export (for example from SIIMS) to this layout. A file-level error rejects the file. A row-level error creates an exception and the rest of the file loads. |
| I2 Event interpreter | Request: note text and today's date. Response must be JSON with event type (from a fixed list), start and end date, direction (higher or lower), magnitude (small, moderate, large), and a rationale of 200 characters or fewer. Dates must fall from yesterday to 14 days ahead. An invalid response gets one retry, then becomes an exception and the manager is asked to rewrite the note. The response is stored only as "proposed." |
| I3 Forecast | Request: item, horizon, features. Response: per day 10th, 50th, 90th percentile demand and model version. If the service fails, the baseline forecast is used and every dependent flag says so. |
| I4 Risk | Request: lots with stock and forecasts. Response: one flag per lot at or above the threshold, with projected unsold (low, point, high) and references to its basis. |
| I5 Dashboard | Read flags, candidates, exceptions, and reports. Write notes, confirmations, edits, rejections, reviews, dismissals, and action records. No operation writes outside C2. |

**Processing rules.** The calculation and data-handling rules in Section 4.2 apply. In addition:
- **Event features.** A confirmed event adds its type, direction, and magnitude to the forecast features for its dates. The model learns the size of each effect from comparable past events in the history.
- **Flag decision.** A lot is flagged on the 50th-percentile projection. The low and high values come from the 90th and 10th percentile demand and are shown as a range.

**Control logic, daily run.** (1) Ingest and validate. (2) Interpret any pending notes. (3) Forecast, using the baseline if the model service fails. (4) Run the risk engine. (5) Publish to the dashboard. Weekly, after the daily run: (6) calibrate against discards, backtest the model against the baseline, and detect recurring patterns. Each stage records its status. A failed stage stops the stages that depend on it, and the dashboard then shows the last good results with their age.

**Error and exception handling.** Data-handling conditions (missing sales, missing expiration date, unmatched discards, short history, and unavailable context signals) follow the rules in Section 4.2. The service-level conditions are:

| Condition | Behavior |
|---|---|
| File missing or unreadable | Reject the file, raise an exception, show the stale banner if no valid data arrived. |
| Row invalid or unmatched | Exception queue, record not used. |
| Interpreter returns invalid output | One retry, then exception and a request to rewrite the note. |
| Model service fails or loses to the baseline in the backtest | Use the baseline forecast and label it. |
| Daily run fails | Last successful results with a banner showing their age. |

### 7.4 How Information Moves

1. **Intake.** Daily files enter through C1. Valid records are stored with a file reference, and invalid ones become exceptions that the manager sees in C7.
2. **Events.** The manager types a note in C7, C3 proposes a structured candidate, and the manager confirms, edits, or rejects it. Only a confirmed or edited event reaches C4. The original note and any edit are kept.
3. **Forecasts and flags.** C4 writes forecasts labeled tier 2. C5 reads lots and forecasts and writes flags that store references to the lot, forecast rows, events used, and the stock-allocation assumption, so every number on a flag can be traced.
4. **Review, correction, and status.** The manager reads the ranked list and a flag's basis, then reviews or dismisses it with a reason and records any action taken outside the system. A correction to a lot or event record is stored beside the original, not over it. A flag moves from open to reviewed or dismissed, and to expired once its lot passes its expiration date.
5. **Calibration and outputs.** Weekly, C6 compares each item's projected unsold quantity with the discard log and records the variance. The outputs are the ranked flag list, the calibration and backtest reports, and the recurring-pattern list. None triggers an action.

## 8. Implementation Guidelines

### 8.1 Implementation Order

| Step | Build | Depends on | Done when |
|---|---|---|---|
| 1 | Synthetic data generator with known injected effects (weekday, holiday, events, several lots per item, discards) | None | Parameters are documented, so every later test has a known right answer. |
| 2 | Data store, ingestion, and exception queue (C1, C2) | 1 | E1, E2 pass. |
| 3 | Baseline forecast and lot risk engine (C5) | 2 | E3 passes for S1 and S2. |
| 4 | ML forecast and backtest (C4, part of C6) | 3 | E4 reports the model beside the baseline. |
| 5 | Context signals, event interpreter, and confirmation gate (C3) | 4 | E5 and E6 pass. |
| 6 | Dashboard review and action log (C7, C8) | 3 | E7, E10, E12, E13, E14 pass. |
| 7 | Weekly calibration and pattern detection (C6) | 4, 6 | E8 passes. |
| 8 | Failure handling and performance | 1 to 7 | E9, E11 pass. |

The baseline forecast comes first so the system works end to end early and the ML model has something to beat.

### 8.2 Validation Priorities and Test Evidence

The first three are the highest priority because they show the core capability is correct and safe.

| ID | Evidence the prototype must produce | Covers |
|---|---|---|
| E1 | A two-line delivery for one item is stored as two lots. | FR-1 |
| E2 | Removing sales days produces a gap and an exception, never zeros. | FR-2, FR-11, S4 |
| E3 | Flags and ranking for S1 and S2 match hand calculations. | FR-5, FR-6 |
| E4 | Backtest reports the forecast's mean absolute error beside the baseline's, and the baseline is used if the model is worse. | FR-4, NFR-8 |
| E5 | An unconfirmed event leaves the forecast unchanged, and a confirmed one changes it as in S3. | FR-3, NFR-6, S3 |
| E6 | On at least 30 labeled synthetic notes, report the schema-valid rate and the event-type accuracy. Initial targets are 95% and 85%. Invalid outputs become exceptions. | FR-3 |
| E7 | Review, dismissal, and action are logged, and no connection to ordering, pricing, or POS exists. | FR-9, NFR-5, NFR-9, S6 |
| E8 | The calibration report shows projected against discarded quantity and a three-week pattern, and makes no lot-level claim, since the scan carries no expiration date. | FR-10, S5 |
| E9 | A forced stage failure shows the stale banner with the age of the last good run. | NFR-7 |
| E10 | Unauthenticated and unassigned users are denied, and employee identifiers appear in no output. | NFR-4 |
| E11 | A daily run over 500 synthetic items finishes within 30 minutes. | NFR-1 |
| E12 | 25 flags fit one screen, each with a reason of two sentences or fewer. | NFR-2 |
| E13 | A sample of flags resolves to its lot, forecast, events, and allocation assumption. | FR-7, NFR-3 |
| E14 | Every forecast, estimate, and flag shown is labeled tier 2. | FR-8, NFR-6 |

### 8.3 AI-Assisted Development Boundaries

| AI may | AI must not |
|---|---|
| Draft boilerplate, the synthetic data generator, tests, and dashboard scaffolding, all of which I review and run | Change a requirement, threshold, or window without a backtest result behind the change |
| Suggest model features and interface details | Produce or describe validation results that I have not run |
| Help write prompts for the event interpreter | Be called at runtime by any component except C3, or receive anything other than the note text |
| Propose test cases | Approve its own output, since every generated artifact needs my review and a passing test |

Prompts and model versions are kept in the repository, and AI assistance is logged in the repository as it is here in Appendix A.

### 8.4 Requirements Traceability

| Requirement | Components | Interfaces and flows | Controls | Evidence |
|---|---|---|---|---|
| FR-1 | C1, C2 | I1 | K1 | E1 |
| FR-2 | C1, C2 | I1 | K1 | E2 |
| FR-3 | C3, C7 | I2, I5, flow 2 | K2 | E5, E6 |
| FR-4 | C4 | I3 | K3 | E4 |
| FR-5 | C5 | I4 | K4 | E3 |
| FR-6 | C5, C7 | I4, I5 | K4 | E3 |
| FR-7 | C5, C7 | I4, flow 3 | K3 | E13 |
| FR-8 | C4, C5, C7 | I3, I4, I5 | K3 | E14 |
| FR-9 | C7, C8 | I5, flow 4 | K4, K5 | E7 |
| FR-10 | C6 | flow 5 | K6 | E8 |
| FR-11 | C1, C7 | I1, I5 | K1 | E2 |
| NFR-1 | C1 to C5 | Daily run | K6 | E11 |
| NFR-2 | C7 | I5 | K3 | E12 |
| NFR-3 | C2, C5, C6 | Flows 3 and 5 | K3 | E13 |
| NFR-4 | C1, C8 | All | K1 | E10 |
| NFR-5 | C7, C8 | I5 | K4, K5 | E7 |
| NFR-6 | C3, C4, C7 | I2, I3 | K2, K3 | E5, E14 |
| NFR-7 | C6, C7 | Daily run | K6 | E9 |
| NFR-8 | C4, C6 | I3, weekly run | K3 | E4 |
| NFR-9 | C5, C7, C8 | I5, flow 4 | K5 | E7 |

### 8.5 Changes to the Assignment 1 Requirements from the Design Work

Four requirements changed during the design work (FR-3, FR-4, NFR-4, NFR-6), and NFR-9 (review status) was added. Appendix B records the reason and effect of each. The limitations in Section 2.10 still apply to the prototype.

## Appendix A. Record of AI Assistance

I used Claude as an assistant for problem selection, drafting, and consistency checks. I made each decision.

| Activity | AI contribution (candidate) | My decision |
|---|---|---|
| Problem selection | Proposed eight candidate problems across domains. | Chose grocery shrink because I have direct experience with it. |
| Problem framing | Framed it as general perishable spoilage. | Corrected it: fresh shrink is shelf-life driven, grocery shrink is theft driven, and counts differ by department. Chose the deli and excluded theft. |
| Requirements | Drafted the first requirements and loss triggers. | Confirmed the assumptions from experience, then corrected them: discards are scanned daily, markdown is not practiced, and the manager ranks by days until expiration. |
| Grading feedback | Mapped each grader comment to the rubric and to Assignment 1's text. | Chose the revisions below. |
| Forecasting approach | Recommended a hybrid: a trailing-average forecast plus an AI-proposed event adjustment, and described the cost of full machine learning. | Chose full ML forecasting because outside events affect sales. I accepted the validation limits in 2.10. |
| Rejected output | Claimed SKU-level discard entries could confirm a specific prediction. | Rejected it after the grader's comment. FR-10 now claims item-level calibration only. |
| Interface and event input (Assignment 2) | Offered a web dashboard or a spreadsheet, and LLM interpretation of free-text notes or a structured form. | Chose the dashboard so review status and action logging can be enforced, and LLM interpretation behind a confirmation gate, which gives GenAI one narrow, justified role. |
| Architecture and design detail (Assignment 2) | Proposed alternatives A to D, the component decisions in 7.1, and drafts of the interface contracts, error handling, and evidence list. | Chose the batch pipeline, made the model, store, and interface decisions, and reviewed the drafts against my requirements. Thresholds and windows remain starting values to tune. |

**Validation I did myself:** checked each assumption against my own experience and my family member's account, and checked the revised requirements against the grader's comments. **Not yet validated:** field-level data formats (2.6), the initial thresholds and windows in 4.2, the interface contracts and accuracy targets in 7.3 and 8.2, and any real-data forecast accuracy.

## Appendix B. Revision Log

| Change | Reason | Effect on the design |
|---|---|---|
| Stock tracked per lot | Grader: multiple expiration batches per item. Receiving carries expiration per delivery line. | FR-1, FR-5, 4.2. |
| Full ML forecast with confirmed outside signals | Grader: need for GenAI over plain calculation unclear. Outside events affect sales. | FR-3, FR-4, NFR-6, NFR-8. Adds a model component, event inputs, and backtesting. |
| Discard validation at item level, with discards allocated to the oldest lot | Grader: item-level discards cannot confirm a specific prediction. Discard scans carry no expiration date, as reported by my family member. | FR-10, 2.10, 4.2, E8. |
| Calculation, window, threshold, and missing-data rules defined | Grader: stock calculations, forecasting windows, and missing-data handling undefined. | Section 4.2, FR-11, NFR-7. |
| Discovery, data availability, alternatives, scenarios, priorities, and limitations added | Grader and rubric: discovery with a real user, data availability, alternatives, representative scenarios, priorities, remaining limitations. | Sections 2.1, 2.6, 2.7, 2.8, 2.10, 4.1. |
| Generic source-file contract with an adapter per source | I found no public documentation of SIIMS to verify its exports. | I1 and 2.6. |
| AI-assistance record added | Assignment 1 and Assignment 2 instructions. | Appendix A. |
| FR-3 handles invalid interpreter output | The interpreter can return unusable output. | Retry once, then an exception (I2, E6). |
| FR-4 falls back to the labeled baseline forecast | A forecast failure should not silence all flags. | I3 and the error-handling table. |
| NFR-4 drops employee identifiers at ingestion | Less personal data is safer than controlling access to it. | C1 and E10. |
| NFR-6 limits runtime GenAI to the event interpreter, sending only note text | Keeps store data away from an external model. | 7.2 and 8.3. |
| NFR-9 added (review status) | Assignment 2 lists review status as a quality attribute. | Section 5, 8.4, E7. |
| Executive Summary rewritten; Sections 6 to 8 added | Assignment 2 deliverable. | Sections 1 and 6 to 8. |
