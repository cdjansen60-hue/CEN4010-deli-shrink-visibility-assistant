"""Synthetic data generator (build step 1).

Writes CSV feeds (items, receiving, sales, discards, notes) plus a truth/ folder
that the pipeline never reads. Parameter values come from
docs/synthetic-data-spec.md and are starting values to tune against the backtest.

Quantities are held as whole "steps" internally (0.25 lb or 1 count) so
rounding to the selling unit never produces float drift.

Usage:
    python -m src.generate_data --items 40 --weeks 26 --seed 42 --out data/generated
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import holidays
import numpy as np

# ---------------------------------------------------------------- spec values
WEEKDAY = [0.85, 0.85, 0.90, 0.95, 1.20, 1.35, 0.90]  # Mon..Sun
SKEW_GROUPS = [(1.5, 0.25), (1.0, 0.50), (0.0, 0.25)]  # (k, share of items)
NOISE_RANGE = (0.10, 0.15)
SHELF_SHORT = (3, 5)       # 40% of items
SHELF_LONG = (6, 10)       # 60% of items
DELIVERY_GAP = (4, 6)      # days between deliveries
STEP = {"lb": 0.25, "ct": 1.0}

HOLIDAY_LIFT = {"Memorial": 1.40, "Independence": 1.40, "Labor": 1.40,
                "Thanksgiving": 1.50, "Christmas": 1.50}
HOLIDAY_DIP_AFTER = ("Thanksgiving", "Christmas")  # x0.70 the next day
PRE_HOLIDAY_RAMP = 1.15
DIP = 0.70

# type: (multiplier, also applies the day before)
EVENT_EFFECT = {"home_game": (1.25, True), "festival": (1.30, False),
                "severe_weather": (0.80, False), "promotion": (1.15, False)}
EVENT_COUNTS = {"home_game": 7, "festival": 5, "severe_weather": 4, "promotion": 4}
N_NON_EVENT, N_AMBIGUOUS = 10, 5
DEFECT_COUNT = (3, 5)      # inclusive, per defect type
DAMAGE_RATE = 0.01         # chance per item-day of a random extra discard
S3_NOTE = "high school playoff game Friday night."

POOL = (
    [(n, "lb") for n in (
        "Sliced ham", "Oven roasted chicken breast", "Genoa salami", "Provolone cheese",
        "Swiss cheese", "American cheese", "Sharp cheddar", "Pastrami", "Corned beef",
        "Bologna", "Honey ham", "Smoked turkey", "Roast turkey", "Pepper jack cheese",
        "Potato salad", "Coleslaw", "Chicken salad", "Tuna salad", "Egg salad",
        "Pasta salad", "Three bean salad", "Cucumber salad", "Hummus", "Pimento cheese",
        "Baked beans", "Mashed potatoes")]
    + [(n, "ct") for n in (
        "Rotisserie chicken", "Turkey sandwich", "Italian sandwich",
        "Ham and cheese sandwich", "Chicken Caesar wrap", "Veggie wrap",
        "Party tray cold cuts", "Mac and cheese cup", "Chicken noodle soup cup",
        "Tomato soup cup", "Cheese pizza slice", "Fried chicken tenders box",
        "Egg roll", "Deviled eggs tray")]
)

NOTE_TEMPLATES = {
    "home_game": [
        "Home football game {day} night, expect a crowd.",
        "Homecoming game this {day}.",
        "Local team has a big home game {day}.",
        "Basketball regional at the high school on {day}."],
    "festival": [
        "Town food festival downtown on {day}.",
        "Street fair {day} near the store.",
        "Community festival at the park {day}, lots of foot traffic.",
        "Farmers market and festival {day}."],
    "severe_weather": [
        "Storm forecast for {day}, local advisory out.",
        "Heavy rain and wind expected {day}.",
        "Ice warning {day}, roads closed.",
        "Tropical storm watch, expecting a slow {day}."],
    "promotion": [
        "Deli promo on sliced meats {day}.",
        "Sale on party trays {day}.",
        "Store promotion {day}: buy one get one on salads.",
        "Ad flyer runs {day}, deli items featured."],
}
NON_EVENT_NOTES = [
    "Slicer was cleaned and serviced.", "Delivery truck arrived late.",
    "New hire starts Monday.", "Case lights replaced.",
    "Reminder: update labels on prepared foods.", "Health inspection passed last week.",
    "Ran out of gloves this morning.", "Back door sticky, maintenance called.",
    "Switched cheese supplier, same price.", "Break room fridge is broken."]
AMBIGUOUS_NOTES = [
    "Might be a game this weekend, not sure.", "Heard it could rain Thursday, maybe.",
    "Someone said there's a fair next month sometime.",
    "Corporate may run a promo, no dates yet.", "Big crowd last Saturday, not sure why."]


# ------------------------------------------------------------------ structures
@dataclass
class Item:
    item_id: str
    name: str
    unit: str
    base: float        # expected steps per day before multipliers
    k: float
    shelf: int
    noise: float
    first_day: dt.date
    anchor: str | None = None

    @property
    def step(self) -> float:
        return STEP[self.unit]


def qty_str(item_unit: str, steps: int) -> str:
    return format(steps * STEP[item_unit], "g")


# --------------------------------------------------------------------- setup
def make_items(rng, n, start, end, weeks):
    items = []
    order = rng.permutation(len(POOL))
    n_weekend, n_flat = round(0.25 * n), round(0.25 * n)
    ks = [1.5] * n_weekend + [0.0] * n_flat + [1.0] * (n - n_weekend - n_flat)
    ks = [ks[i] for i in rng.permutation(n)]
    short_hist = {}
    if n >= 10 and weeks >= 8:
        picks = rng.choice(n, 4, replace=False)
        short_hist = {int(picks[0]): 3, int(picks[1]): 3, int(picks[2]): 6, int(picks[3]): 6}
    for i in range(n):
        name, unit = POOL[order[i]] if i < len(POOL) else (
            f"Deli item {i + 1:03d}", ["lb", "ct"][int(rng.integers(0, 2))])
        lo, hi = (3, 14) if unit == "lb" else (8, 36)
        shelf = int(rng.integers(SHELF_SHORT[0], SHELF_SHORT[1] + 1)) if rng.random() < 0.4 \
            else int(rng.integers(SHELF_LONG[0], SHELF_LONG[1] + 1))
        first = start
        if i in short_hist:
            first = end - dt.timedelta(days=short_hist[i] * 7 - 1)
        items.append(Item(f"ITM{i + 1:03d}", name, unit, rng.uniform(lo, hi) / STEP[unit],
                          ks[i], shelf, rng.uniform(*NOISE_RANGE), first))
    # Scenario anchors S1 to S3: hand-placed cases for E3, so the right answer can be
    # worked out on paper. Demand is stated in lb/day (base = lb / 0.25 lb per step).
    #   S1: one lot, 12 lb expiring as_of+5 at 1.6 lb/day, so about 4 lb projected unsold.
    #   S2: two lots (A 6 lb expiring as_of+2, B 8 lb expiring as_of+6) at 2 lb/day.
    #       Oldest-first sales leave about 2 lb of A unsold and B about even.
    #   S3: one 9 lb lot expiring the Sunday after the playoff game note (event path).
    # Their regular deliveries stop early (see simulate_item), so the lots below are
    # their only open stock. S3's 1.5 lb/day demand is my choice, not in the spec.
    items += [
        Item("S1", "Sliced turkey breast", "lb", 1.6 / 0.25, 0.0, 5, 0.12, start, "S1"),
        Item("S2", "Sliced roast beef", "lb", 2.0 / 0.25, 0.0, 6, 0.12, start, "S2"),
        Item("S3", "Macaroni salad", "lb", 1.5 / 0.25, 1.0, 5, 0.12, start, "S3"),
    ]
    return items


def holiday_factors(start, end):
    hol = holidays.US(years=range(start.year, end.year + 1), observed=False)
    f = defaultdict(lambda: 1.0)
    one = dt.timedelta(days=1)
    for day, name in hol.items():
        if "After" in name:
            continue
        for key, lift in HOLIDAY_LIFT.items():
            if key in name:
                f[day] *= lift
                f[day - one] *= PRE_HOLIDAY_RAMP
                if key in HOLIDAY_DIP_AFTER:
                    f[day + one] *= DIP
    return f


def make_notes(rng, start, end, as_of):
    """Returns (notes, event_factor). notes: list of dicts incl. truth fields."""
    days = [start + dt.timedelta(days=i) for i in range(3, (end - start).days)]
    used, notes = set(), []
    factor = defaultdict(lambda: 1.0)

    def pick(cands):
        cands = [d for d in cands if d not in used]
        d = cands[int(rng.integers(0, len(cands)))]
        used.add(d)
        return d

    for etype, count in EVENT_COUNTS.items():
        cands = [d for d in days if d.weekday() in (4, 5)] if etype == "home_game" else days
        mult, day_before = EVENT_EFFECT[etype]
        for _ in range(count):
            d = pick(cands)
            text = NOTE_TEMPLATES[etype][int(rng.integers(0, 4))].format(day=d.strftime("%A"))
            factor[d] *= mult
            affected = [d]
            if day_before:
                factor[d - dt.timedelta(days=1)] *= mult
                affected.append(d - dt.timedelta(days=1))
            notes.append(dict(note_date=max(start, d - dt.timedelta(days=int(rng.integers(1, 4)))),
                              note_text=text, label="event", event_type=etype,
                              event_date=d, multiplier=mult,
                              days_affected=";".join(x.isoformat() for x in affected)))
    for text, label in ([(t, "non_event") for t in NON_EVENT_NOTES[:N_NON_EVENT]]
                        + [(t, "ambiguous") for t in AMBIGUOUS_NOTES[:N_AMBIGUOUS]]):
        notes.append(dict(note_date=days[int(rng.integers(0, len(days)))], note_text=text,
                          label=label, event_type="", event_date="", multiplier="",
                          days_affected=""))
    # S3: the playoff game falls after the history, so it has no effect on past demand.
    friday = as_of + dt.timedelta(days=(4 - as_of.weekday()) % 7)
    notes.append(dict(note_date=as_of, note_text=S3_NOTE, label="event", event_type="home_game",
                      event_date=friday, multiplier=1.25,
                      days_affected=f"{friday - dt.timedelta(days=1)};{friday}".replace(" ", ""),
                      scenario="S3"))
    notes.sort(key=lambda n: (n["note_date"], n["note_text"]))
    for i, n in enumerate(notes, 1):
        n["note_id"] = f"N{i:03d}"
    return notes, factor, friday


# ---------------------------------------------------------------- simulation
def take(lots, qty, field):
    """Oldest-expiration-first allocation. Returns [(lot, n)]."""
    taken = []
    for lot in sorted(lots, key=lambda l: (l["exp"], l["delivery"])):
        if qty == 0:
            break
        n = min(qty, lot["rem"])
        if n:
            lot["rem"] -= n
            lot[field] += n
            qty -= n
            taken.append((lot, n))
    return taken


def simulate_item(item, end, hol, ev, rng):
    res = dict(lots=[], sales=[], discards=[], stockouts=[], demand=[], zero_days=[])
    lots, next_del, day = [], item.first_day, item.first_day
    one = dt.timedelta(days=1)
    while day <= end:
        if day == next_del:
            gap = int(rng.integers(DELIVERY_GAP[0], DELIVERY_GAP[1] + 1))
            next_del = day + dt.timedelta(days=gap)
            qty = max(1, int(round(item.base * min(gap, item.shelf) * rng.uniform(0.95, 1.35))))
            # Anchors stop regular deliveries so their hand-placed lots are the only open stock.
            if item.anchor is None or day <= end - dt.timedelta(days=item.shelf):
                lot = dict(item=item, delivery=day, exp=day + dt.timedelta(days=item.shelf),
                           recv=qty, rem=qty, sold=0, discarded=0, special=False)
                lots.append(lot)
                res["lots"].append(lot)
        if sum(l["rem"] for l in lots) == 0:
            res["zero_days"].append(day)
        wk = 1 + item.k * (WEEKDAY[day.weekday()] - 1)
        expected = item.base * wk * hol[day] * ev[day]
        true = max(0, int(round(expected * (1 + rng.normal(0, item.noise)))))
        stock = sum(l["rem"] for l in lots)
        sold = min(true, stock)
        take(lots, sold, "sold")
        if true > sold:
            res["stockouts"].append((item, day, true - sold))
        res["sales"].append((item, day, sold))
        res["demand"].append((item, day, expected, true, WEEKDAY[day.weekday()], hol[day], ev[day]))
        if rng.random() < DAMAGE_RATE and sum(l["rem"] for l in lots) > 0:
            q = min(sum(l["rem"] for l in lots), int(rng.integers(1, int(round(1 / item.step)) + 1)))
            res["discards"].append((item, day, q, "damage", take(lots, q, "discarded")))
        for lot in lots:
            if lot["exp"] == day and lot["rem"] > 0:
                q = lot["rem"]
                lot["rem"], lot["discarded"] = 0, lot["discarded"] + q
                res["discards"].append((item, day, q, "expired", [(lot, q)]))
        lots = [l for l in lots if l["exp"] > day and l["rem"] > 0]
        day += one
    return res


# ------------------------------------------------------------------- output
def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def generate(out_dir, n_items=40, weeks=26, seed=42, start=dt.date(2026, 5, 18)):
    out = Path(out_dir)
    rng = np.random.default_rng(seed)
    end = start + dt.timedelta(days=weeks * 7 - 1)
    as_of = end + dt.timedelta(days=1)
    items = make_items(rng, n_items, start, end, weeks)
    hol = holiday_factors(start, end)
    notes, ev, friday = make_notes(rng, start, end, as_of)

    sims = [simulate_item(it, end, hol, ev, rng) for it in items]
    lots = [l for s in sims for l in s["lots"]]
    sales = [dict(item_id=i.item_id, sale_date=d, qty_sold=q, _unit=i.unit, _item=i)
             for s in sims for (i, d, q) in s["sales"]]
    discards = [dict(item_id=i.item_id, discard_date=d, qty=q, _unit=i.unit, _item=i,
                     _reason=r, _src=src)
                for s in sims for (i, d, q, r, src) in s["discards"]]

    # Hand-placed S1 to S3 lots (see make_items), received on the as-of morning, after
    # the sales history. Sizes are in steps (quarter-lb), written as lb * 4.
    sunday = friday + dt.timedelta(days=2)
    by_id = {i.item_id: i for i in items}
    special = [("S1", 12 * 4, as_of + dt.timedelta(days=5)),
               ("S2", 6 * 4, as_of + dt.timedelta(days=2)),
               ("S2", 8 * 4, as_of + dt.timedelta(days=6)),
               ("S3", 9 * 4, sunday)]
    for iid, steps, exp in special:
        lots.append(dict(item=by_id[iid], delivery=as_of, exp=exp, recv=steps, rem=steps,
                         sold=0, discarded=0, special=True))

    # Defect: a discard for an item with no stock that day.
    anchors = {"S1", "S2", "S3"}
    zero = [(i, d) for s, it in zip(sims, items) if it.item_id not in anchors
            for i in [it] for d in s["zero_days"]]
    for _ in range(int(rng.integers(DEFECT_COUNT[0], DEFECT_COUNT[1] + 1))):
        if zero:
            it, d = zero.pop(int(rng.integers(0, len(zero))))
            discards.append(dict(item_id=it.item_id, discard_date=d, qty=int(round(1 / it.step)),
                                 _unit=it.unit, _item=it, _reason="no_matching_stock", _src=[]))
    # Assign ids in date order.
    lots.sort(key=lambda l: (l["delivery"], l["item"].item_id))
    for n, lot in enumerate(lots, 1):
        lot["line_id"] = f"RCV{n:05d}"
    discards.sort(key=lambda r: (r["discard_date"], r["item_id"]))
    emps = [f"E{1000 + int(x)}" for x in rng.choice(900, 12, replace=False)]
    for n, r in enumerate(discards, 1):
        r["scan_id"] = f"DSC{n:05d}"
        r["employee_id"] = emps[int(rng.integers(0, len(emps)))]
    sales.sort(key=lambda r: (r["sale_date"], r["item_id"]))

    receiving = [dict(line_id=l["line_id"], item_id=l["item"].item_id,
                      delivery_date=l["delivery"], received_qty=l["recv"], _unit=l["item"].unit,
                      expiration_date=l["exp"], _special=l["special"], _lot=l) for l in lots]

    defects, touched = [], set()

    def log(kind, feed, key, detail=""):
        defects.append(dict(defect_type=kind, feed=feed, row_key=key, detail=detail))

    def count():
        return int(rng.integers(DEFECT_COUNT[0], DEFECT_COUNT[1] + 1))

    for r in discards:
        if r["_reason"] == "no_matching_stock":
            touched.add(id(r))
            log("unmatched_discard", "discards", r["scan_id"], r["item_id"])
    # Defect: missing sales days (the row is gone; it is never a zero).
    cands = [r for r in sales if r["item_id"] not in anchors
             and start + dt.timedelta(days=14) <= r["sale_date"] <= end]
    for idx in sorted(rng.choice(len(cands), count(), replace=False), reverse=True):
        r = cands[int(idx)]
        sales.remove(r)
        log("missing_sales_day", "sales", f"{r['item_id']}|{r['sale_date']}")
    # Defect: delivery line with no expiration date.
    cands = [r for r in receiving if r["item_id"] not in anchors]
    for idx in rng.choice(len(cands), count(), replace=False):
        r = cands[int(idx)]
        touched.add(id(r))
        log("missing_expiration", "receiving", r["line_id"])
        r["expiration_date"] = ""
    # Defect: malformed rows (corrupted in place, original value logged).
    feeds = {"sales": (sales, "qty_sold", "sale_date", lambda r: f"{r['item_id']}|{r['sale_date']}"),
             "receiving": (receiving, "received_qty", "delivery_date", lambda r: r["line_id"]),
             "discards": (discards, "qty", "discard_date", lambda r: r["scan_id"])}
    kinds = ["negative_qty", "non_numeric_qty", "bad_date", "blank_item_id"]
    for n in range(count()):
        feed = list(feeds)[n % 3]
        rows, qf, df, keyf = feeds[feed]
        pool = [r for r in rows if r["item_id"] not in anchors and id(r) not in touched
                and not r.get("_special")]
        r = pool[int(rng.integers(0, len(pool)))]
        touched.add(id(r))
        kind = kinds[int(rng.integers(0, len(kinds)))]
        key = keyf(r)
        if kind == "negative_qty":
            r["_bad"] = (qf, "-" + (qty_str(r["_unit"], r[qf]) if r[qf] else "1"))
        elif kind == "non_numeric_qty":
            r["_bad"] = (qf, "abc")
        elif kind == "bad_date":
            r["_bad"] = (df, "2026-13-45")
        else:
            r["_bad"] = ("item_id", "")
        log("malformed_row", feed, key, f"{kind} (was {r[r['_bad'][0]]})")

    def render(rows, qf, dfields):
        res = []
        for r in rows:
            d = {k: v for k, v in r.items() if not k.startswith("_")}
            d[qf] = qty_str(r["_unit"], r[qf])
            for f in dfields:
                d[f] = d[f].isoformat() if hasattr(d[f], "isoformat") else d[f]
            if "_bad" in r:
                d[r["_bad"][0]] = r["_bad"][1]
            res.append(d)
        return res

    write_csv(out / "items.csv", ["item_id", "description", "selling_unit"],
              [dict(item_id=i.item_id, description=i.name, selling_unit=i.unit) for i in items])
    write_csv(out / "receiving.csv",
              ["line_id", "item_id", "delivery_date", "received_qty", "expiration_date"],
              render(receiving, "received_qty", ["delivery_date", "expiration_date"]))
    write_csv(out / "sales.csv", ["item_id", "sale_date", "qty_sold"],
              render(sales, "qty_sold", ["sale_date"]))
    write_csv(out / "discards.csv", ["scan_id", "item_id", "discard_date", "qty", "employee_id"],
              render(discards, "qty", ["discard_date"]))
    write_csv(out / "notes.csv", ["note_id", "note_date", "note_text"],
              [dict(n, note_date=n["note_date"].isoformat()) for n in notes])

    t = out / "truth"
    write_csv(t / "items_truth.csv",
              ["item_id", "base_demand_units", "weekday_skew_k", "shelf_life_days",
               "first_history_day", "anchor"],
              [dict(item_id=i.item_id, base_demand_units=round(i.base * i.step, 3),
                    weekday_skew_k=i.k, shelf_life_days=i.shelf,
                    first_history_day=i.first_day.isoformat(), anchor=i.anchor or "")
               for i in items])
    write_csv(t / "demand_truth.csv",
              ["item_id", "date", "expected_demand", "true_demand", "weekday_mult",
               "holiday_factor", "event_factor"],
              [dict(item_id=i.item_id, date=d.isoformat(), expected_demand=round(e * i.step, 3),
                    true_demand=format(q * i.step, "g"), weekday_mult=w, holiday_factor=h,
                    event_factor=round(v, 4))
               for s in sims for (i, d, e, q, w, h, v) in s["demand"]])
    write_csv(t / "lots_truth.csv",
              ["line_id", "item_id", "delivery_date", "expiration_date", "received", "sold",
               "discarded", "remaining", "hand_placed"],
              [dict(line_id=l["line_id"], item_id=l["item"].item_id,
                    delivery_date=l["delivery"].isoformat(), expiration_date=l["exp"].isoformat(),
                    received=qty_str(l["item"].unit, l["recv"]),
                    sold=qty_str(l["item"].unit, l["sold"]),
                    discarded=qty_str(l["item"].unit, l["discarded"]),
                    remaining=qty_str(l["item"].unit, l["recv"] - l["sold"] - l["discarded"]),
                    hand_placed=l["special"]) for l in lots])
    write_csv(t / "discards_truth.csv", ["scan_id", "reason", "source_lines"],
              [dict(scan_id=r["scan_id"], reason=r["_reason"],
                    source_lines=";".join(f"{l['line_id']}:{qty_str(r['_unit'], n)}"
                                          for l, n in r["_src"])) for r in discards])
    write_csv(t / "stockouts_truth.csv", ["item_id", "date", "unmet_demand"],
              [dict(item_id=i.item_id, date=d.isoformat(), unmet_demand=format(q * i.step, "g"))
               for s in sims for (i, d, q) in s["stockouts"]])
    write_csv(t / "events_truth.csv",
              ["note_id", "label", "event_type", "event_date", "multiplier", "days_affected",
               "scenario"],
              [dict(n, event_date=n["event_date"].isoformat() if n["event_date"] else "")
               for n in notes])
    write_csv(t / "defects.csv", ["defect_type", "feed", "row_key", "detail"], defects)
    with open(t / "scenarios.json", "w", encoding="utf-8") as fh:
        json.dump({
            "as_of": as_of.isoformat(), "history_end": end.isoformat(),
            "S1": "12 lb lot expiring as_of+5, demand 1.6 lb/day",
            "S2": "lot A 6 lb expiring as_of+2, lot B 8 lb expiring as_of+6, demand 2 lb/day",
            "S3": f"9 lb lot expiring {sunday}, playoff game note dated as_of for {friday}, "
                  "demand 1.5 lb/day (my choice, not in the spec)"}, fh, indent=2)

    summary = defaultdict(int)
    for d in defects:
        summary[d["defect_type"]] += 1
    return dict(as_of=as_of.isoformat(), items=len(items), sales_rows=len(sales),
                lots=len(lots), discards=len(discards), notes=len(notes), defects=dict(summary))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--items", type=int, default=40)
    p.add_argument("--weeks", type=int, default=26)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2026, 5, 18))
    p.add_argument("--out", default="data/generated")
    a = p.parse_args()
    print(json.dumps(generate(a.out, a.items, a.weeks, a.seed, a.start), indent=2))


if __name__ == "__main__":
    main()
