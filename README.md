# Value at Risk — and when it fails

By Amin Behrad ([YouTube: Amin Behrad — Risk Models](https://www.youtube.com/@AminBehradRisk)). Built with Claude Code as a coding assistant.

Companion code for the video. A one-day 99% VaR on the S&P 500, built three ways every trading day
from 1986 to 2026 using only the previous 250 days, then backtested against what actually happened.

| File | What it does |
|---|---|
| `data/verify_data.py` | Cross-checks daily closes from Yahoo Finance, FRED and the Wall Street Journal, and builds one series. Every disagreement is listed in `data/VERIFICATION.md`. |
| `var_backtest.py` | Historical, parametric and fat-tailed Monte Carlo VaR; Kupiec and Christoffersen tests; breaches per year against the Basel traffic-light zones. Writes `results/`. |
| `results/summary.md` | The numbers quoted in the video. |

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python data/verify_data.py
.venv/bin/python var_backtest.py
```

Index price data is licensed by its providers, so it is not included here. Download the three files
listed at the top of `data/verify_data.py` into `data/raw/` first.

## Results (1986-01-02 to 2026-09-16)

See [`results/summary.md`](results/summary.md) and the two charts in `results/`.
