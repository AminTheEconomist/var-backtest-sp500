"""Cross-check S&P 500 daily closes from three independent sources and write one verified series.

Sources (downloaded 2026-09-16 into data/raw/):
  1. Yahoo Finance chart API, ^GSPC           -> raw/yahoo_gspc_to_2025-09-16.json (1985-01-02 .. 2025-09-16)
  2. FRED, series SP500 (St. Louis Fed)       -> raw/fred_SP500.csv                (2016-09-19 .. 2026-09-16)
  3. Wall Street Journal historical prices    -> raw/wsj_spx_HistoricalPrices.csv  (1985-01-02 .. 2026-09-16)

Rule (tolerance 1 cent):
  - all sources covering the day agree              -> status "agree_3" or "agree_2"
  - three sources, two agree                         -> majority value, status "majority_2of3"
  - two sources disagree (only happens pre-2016)     -> WSJ value, status "wsj_tiebreak"
WSJ is the tiebreaker because it matched FRED (the Federal Reserve's copy) on every one of their
overlapping days, while Yahoo differed from FRED on some. Every non-"agree" day is listed in VERIFICATION.md.
Raw S&P index data is licensed; data/raw/ and the output CSV are for local use, not for publishing.
"""
import csv, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
TOL = 0.011

def load_yahoo():
    r = json.loads((RAW / "yahoo_gspc_to_2025-09-16.json").read_text())["chart"]["result"][0]
    off = r["meta"]["gmtoffset"]
    closes = r["indicators"]["quote"][0]["close"]
    out = {}
    for ts, c in zip(r["timestamp"], closes):
        if c is None:
            continue
        d = (datetime.fromtimestamp(ts, tz=timezone.utc) + timedelta(seconds=off)).date().isoformat()
        out[d] = round(c, 2)
    return out

def load_fred():
    out = {}
    with open(RAW / "fred_SP500.csv") as f:
        for row in csv.DictReader(f):
            v = row["SP500"].strip()
            if v and v != ".":
                out[row["observation_date"]] = float(v)
    return out

def load_wsj():
    out = {}
    with open(RAW / "wsj_spx_HistoricalPrices.csv") as f:
        rdr = csv.reader(f)
        next(rdr)
        for row in rdr:
            if not row:
                continue
            d = datetime.strptime(row[0].strip(), "%m/%d/%y").date().isoformat()
            out[d] = float(row[4])
    return out

src = {"yahoo": load_yahoo(), "fred": load_fred(), "wsj": load_wsj()}
all_dates = sorted(set().union(*[s.keys() for s in src.values()]))

rows, problems = [], []
pair_stats = {}
for d in all_dates:
    have = {k: v[d] for k, v in src.items() if d in v}
    for a in have:
        for b in have:
            if a < b:
                st = pair_stats.setdefault((a, b), [0, 0, 0.0])
                st[0] += 1
                diff = abs(have[a] - have[b])
                st[1] += diff > TOL
                st[2] = max(st[2], diff)
    vals = list(have.values())
    if max(vals) - min(vals) <= TOL:
        status, value = f"agree_{len(have)}", have.get("wsj", vals[0])
    elif len(have) == 3:
        value = next(v for v in vals if sum(abs(v - w) <= TOL for w in vals) >= 2)
        status = "majority_2of3"
    else:
        status, value = "wsj_tiebreak", have["wsj"]
    if len(have) < 2:
        status = "single_source"
    rows.append((d, value, status))
    if not status.startswith("agree") or len(have) < 2:
        problems.append((d, have, status))
verified = rows
lines = ["# S&P 500 daily close — verification report", "",
         f"Built by `data/verify_data.py` on {datetime.now().date().isoformat()}. Tolerance: 1 cent.", "",
         "| Source | Days | First | Last |", "|---|---|---|---|"]
for k, v in src.items():
    ks = sorted(v)
    lines.append(f"| {k} | {len(v):,} | {ks[0]} | {ks[-1]} |")
lines += ["", "## Pairwise agreement on overlapping days", "", "| Pair | Overlapping days | Days differing > 1 cent | Largest difference |", "|---|---|---|---|"]
for (a, b), (n, bad, mx) in sorted(pair_stats.items()):
    lines.append(f"| {a} vs {b} | {n:,} | {bad:,} | {mx:.2f} |")
from collections import Counter
cnt = Counter(r[2] for r in rows)
lines += ["", "## Result", "", f"- Days in the final series: **{len(rows):,}**, {rows[0][0]} to {rows[-1][0]}"]
lines += [f"- `{k}`: {v:,}" for k, v in sorted(cnt.items())]
biggest = max(problems, key=lambda p: (max(p[1].values()) - min(p[1].values())) / min(p[1].values())) if problems else None
if biggest:
    d, have, _ = biggest
    rel = (max(have.values()) - min(have.values())) / min(have.values())
    lines.append(f"- Largest disagreement in relative terms: {d}, {rel:.2%}")
lines += ["", "## Every day where the sources did not all agree", ""]
for d, have, status in problems:
    lines.append(f"- {d} ({status}): " + ", ".join(f"{k}={v}" for k, v in have.items()))
lines += ["", "## Spot checks", ""]
for d in ["1987-10-16", "1987-10-19", "2008-09-29", "2008-10-15", "2020-03-16", "2025-09-16", "2026-09-16"]:
    have = {k: v.get(d) for k, v in src.items()}
    lines.append(f"- {d}: " + ", ".join(f"{k}={v}" for k, v in have.items()))
(HERE / "VERIFICATION.md").write_text("\n".join(lines) + "\n")

with open(HERE / "sp500_daily_close_verified.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "close", "check"])
    w.writerows(rows)
print("\n".join(lines[:40]))
