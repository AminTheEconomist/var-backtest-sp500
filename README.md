# Value at Risk — and when it fails

By Amin Behrad ([YouTube: Amin Behrad — Risk Models](https://www.youtube.com/@AminBehradRisk)). Built with Claude Code as a coding assistant.

Companion code for the video. A one-day 99% VaR on the S&P 500, built three ways every trading day
from 1986 to 2026 using only the previous 250 days, then backtested against what actually happened.

| File | What it does |
|---|---|
| `data/verify_data.py` | Cross-checks daily closes from Yahoo Finance, FRED and the Wall Street Journal, and builds one series. Every disagreement is listed in `data/VERIFICATION.md`. |
| `var_backtest.py` | Historical, parametric and fat-tailed Monte Carlo VaR; Kupiec and Christoffersen tests; breaches per year against the Basel traffic-light zones. Writes `results/`. |
| `results/summary.md` | The numbers quoted in the video. |
| `tests/` | `pytest` suite. The three VaR models, the Kupiec and Christoffersen tests and the Basel zones on toy cases with known answers, plus one full run of `var_backtest.py` on made-up prices. |

## Reproduce in 3 commands

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python data/verify_data.py
.venv/bin/python var_backtest.py
```

Needs Python 3.11 or newer. Index price data is licensed by its providers, so it is not included here.
Download the three files listed at the top of `data/verify_data.py` into `data/raw/` first.

## Run the tests

The tests use made-up prices, so they need no downloads.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest
```

## Results (1986-01-02 to 2026-09-16)

See [`results/summary.md`](results/summary.md) and the two charts in `results/`.

## Methods and limitations

- **Forecast.** Each day's one-day 99% VaR comes from the previous 250 daily returns and nothing later. Returns are simple close-to-close changes in the index level, so dividends are left out.
- **Three models.** Historical is the 1% quantile of those 250 returns. Parametric is 2.326 × their standard deviation, with the mean taken as zero. Monte Carlo draws 10,000 times from a Student-t with 4 degrees of freedom, scaled to the same standard deviation, with a fixed seed (7). The 4 is a choice, not a fitted value, and 10,000 draws leave each day's Monte Carlo VaR with roughly 3% sampling noise.
- **Tests.** A breach is a day when the loss was bigger than the VaR set the day before. Kupiec compares the number of breaches with the 1% expected. Christoffersen asks whether breaches cluster. Kupiec treats breaches as independent, so read the two together.
- **Basel zones** are written for 250-day periods. Here they are applied to calendar years, which have 248 to 254 trading days, and 2026 is a partial year (to 16 September), so its zone is not comparable.
- **Scope.** One index, a one-day horizon, a 250-day window, a 99% level. This says nothing about other indices, horizons, windows or levels.
