# Synthetic Data Generator: Parameter Spec

Build step 1 (report Section 8.1). The generator writes CSV feed files with known injected effects, so every later test has a known right answer. All values here are starting values, to be tuned against the backtest.

## General

| Parameter | Value |
|---|---|
| Items | 40 by default, configurable (`--items 500` for E11) |
| History | 26 weeks by default, configurable |
| Short-history items | A few items with 3 and 6 weeks, to test "insufficient history" |
| Seed | Fixed, configurable. Same seed gives the same data |
| Output | CSV files, one per feed: receiving, sales, discards, plus a ground-truth folder the pipeline never reads |

## Demand

Expected daily demand = item base demand x weekday multiplier x holiday effect x event effect, plus noise.

| Day | Multiplier |
|---|---|
| Mon | 0.85 |
| Tue | 0.85 |
| Wed | 0.90 |
| Thu | 0.95 |
| Fri | 1.20 |
| Sat | 1.35 |
| Sun | 0.90 |

- Each item has its own base demand and selling unit (pounds or count).
- Each item has a skew factor `k`: `multiplier = 1 + k x (table value - 1)`. Weekend-skewed k = 1.5 (10 items), standard k = 1 (20 items), flat k = 0 (10 items). **Confirmed.**
- Noise: 10 to 15%, rounded to the selling unit.

## Holidays

Source: the `holidays` package, US federal holidays.

| Effect | Holidays | Value |
|---|---|---|
| Lift +40% | Memorial Day, July 4, Labor Day | Decided |
| Lift +50% | Thanksgiving, Christmas | Decided |
| Dip -30% | The one day after Thanksgiving and Christmas | Decided |
| Pre-holiday ramp +15% | The day before each lift holiday | Decided |
| Other federal holidays | No effect for now | Decided |

## Events

Each event has a date, a type, and a free-text note. The note is later parsed by the event interpreter (C3) and doubles as labeled data for E6 (30 or more notes).

| Type | Effect |
|---|---|
| Home game | +25% on the day and the day before |
| Community festival | +30% |
| Severe weather | -20% |
| Store promotion | +15% |

- True events and their multipliers go in the ground-truth folder only.
- Include the S3 note: "high school playoff game Friday night."
- Notes: about 35 labeled notes (E6 needs 30 or more). About 20 are real events across the four types with varied wording, and about 15 are non-events or ambiguous notes. **Confirmed.**

## Lots, sales, discards

- One delivery line = one lot: item, delivery date, received quantity, expiration date.
- Expiration = delivery date + item shelf life (3 to 10 days by item). Deliveries every 4 to 6 days.
- Short-shelf-life items (3 to 5 days) will rarely overlap lots and may stock out. Items with 7 to 10 days of shelf life should overlap, so E1 and S2 have multi-lot items.
- Sales: one row per item per day. Sales never exceed stock. A shortfall is recorded as a stockout.
- Discards: leftover at expiration, plus a few random extras (damage, quality). Scan rows carry item, date, quantity, and a fake employee ID. No expiration date and no lot ID. Ground truth remembers the source lot.

## Scenario anchor items

Hand-placed so E3 can compare against hand calculations.

- **S1:** sliced turkey, lot of 12 lb, expires in 5 days, demand 1.6 lb/day.
- **S2:** one item, lot A 6 lb expiring in 2 days, lot B 8 lb expiring in 6, demand 2 lb/day.
- **S3:** lot of 9 lb expiring Sunday, with the playoff game note.

## Injected defects

3 to 5 of each. Every corrupted row is listed in the ground-truth folder so tests know the expected exception count.

- Missing sales days (S4, E2)
- A delivery line with no expiration date
- A discard for an item with no matching stock
- A few malformed rows
