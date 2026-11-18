import csv
import datetime as dt

from src.generate_data import generate


def rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_same_seed_same_data(tmp_path):
    generate(tmp_path / "a", n_items=12, weeks=12, seed=7)
    generate(tmp_path / "b", n_items=12, weeks=12, seed=7)
    for name in ("sales.csv", "receiving.csv", "discards.csv", "notes.csv"):
        assert (tmp_path / "a" / name).read_bytes() == (tmp_path / "b" / name).read_bytes()


def test_scenario_lots(tmp_path):
    info = generate(tmp_path, n_items=12, weeks=12, seed=7)
    as_of = dt.date.fromisoformat(info["as_of"])
    lots = [r for r in rows(tmp_path / "receiving.csv") if r["delivery_date"] == as_of.isoformat()
            and r["item_id"].startswith("S")]
    got = {(r["item_id"], r["received_qty"], (dt.date.fromisoformat(r["expiration_date"]) - as_of).days)
           for r in lots}
    assert {("S1", "12", 5), ("S2", "6", 2), ("S2", "8", 6)} <= got
    s3 = [r for r in lots if r["item_id"] == "S3"][0]
    assert s3["received_qty"] == "9"
    assert dt.date.fromisoformat(s3["expiration_date"]).weekday() == 6  # Sunday


def test_defect_counts_and_notes(tmp_path):
    generate(tmp_path, n_items=12, weeks=12, seed=7)
    counts = {}
    for d in rows(tmp_path / "truth" / "defects.csv"):
        counts[d["defect_type"]] = counts.get(d["defect_type"], 0) + 1
    assert set(counts) == {"missing_sales_day", "missing_expiration", "unmatched_discard",
                           "malformed_row"}
    assert all(3 <= c <= 5 for c in counts.values()), counts
    notes = rows(tmp_path / "notes.csv")
    assert len(notes) >= 30
    assert any(n["note_text"] == "high school playoff game Friday night." for n in notes)


def test_lot_accounting_and_no_employee_ids_in_other_feeds(tmp_path):
    generate(tmp_path, n_items=12, weeks=12, seed=7)
    for lot in rows(tmp_path / "truth" / "lots_truth.csv"):
        assert float(lot["remaining"]) >= 0
        assert float(lot["sold"]) + float(lot["discarded"]) <= float(lot["received"])
    assert "employee_id" not in rows(tmp_path / "sales.csv")[0]
