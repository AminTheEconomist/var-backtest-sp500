"""Value at Risk backtest on the S&P 500, 1986-2026.

Builds a one-day 99% VaR three ways, every trading day, from the previous 250 days only
(no look-ahead), then checks each forecast against what actually happened the next day.

    1. Historical simulation  - the 1% quantile of the last 250 daily returns
    2. Parametric (normal)    - 2.326 x standard deviation of the last 250 returns
    3. Monte Carlo (fat tail) - 10,000 draws from a Student-t (4 degrees of freedom)
                                scaled to the same standard deviation

Tests:
    - Breach count vs the 1% expected (Kupiec proportion-of-failures test)
    - Breach clustering (Christoffersen independence test)
    - Breaches per calendar year, against the Basel traffic-light zones
      (green 0-4, yellow 5-9, red 10+ breaches in 250 days)

Data: data/sp500_daily_close_verified.csv, built by data/verify_data.py from three
independent sources (Yahoo Finance, FRED, Wall Street Journal). The index data is licensed,
so the CSV is not published with this code; run data/verify_data.py on your own downloads.

Run:  .venv/bin/python var_backtest.py      -> writes results/
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "sp500_daily_close_verified.csv"
OUT = HERE / "results"

CONFIDENCE = 0.99
WINDOW = 250                # trading days of history behind each forecast
PORTFOLIO = 1_000_000       # dollars, for reporting VaR in money terms
MC_DRAWS = 10_000
MC_DF = 4                   # Student-t degrees of freedom for the fat-tailed Monte Carlo
SEED = 7


# ---------------------------------------------------------------- data
def load_returns() -> pd.Series:
    prices = pd.read_csv(DATA, parse_dates=["date"], index_col="date")["close"]
    return prices.pct_change().dropna().rename("return")


# ---------------------------------------------------------------- the three VaR models
def var_historical(window: np.ndarray) -> float:
    return -np.quantile(window, 1 - CONFIDENCE)


def var_parametric(window: np.ndarray) -> float:
    z = stats.norm.ppf(CONFIDENCE)                     # 2.326
    return z * window.std(ddof=1)


def var_monte_carlo(window: np.ndarray, rng: np.random.Generator) -> float:
    sigma = window.std(ddof=1)
    t_scale = np.sqrt((MC_DF - 2) / MC_DF)             # makes the t draws have variance 1
    simulated = sigma * t_scale * rng.standard_t(MC_DF, MC_DRAWS)
    return -np.quantile(simulated, 1 - CONFIDENCE)


def rolling_var(returns: pd.Series) -> pd.DataFrame:
    """VaR for day t uses only returns t-250 ... t-1."""
    rng = np.random.default_rng(SEED)
    r = returns.to_numpy()
    rows = []
    for t in range(WINDOW, len(r)):
        w = r[t - WINDOW:t]
        rows.append((var_historical(w), var_parametric(w), var_monte_carlo(w, rng)))
    return pd.DataFrame(rows, index=returns.index[WINDOW:],
                        columns=["historical", "parametric", "monte_carlo"])


# ---------------------------------------------------------------- tests
def kupiec_pof(breaches: int, days: int, p: float = 1 - CONFIDENCE) -> float:
    """p-value of 'the true breach rate is p'. Small p-value -> the model is wrong about frequency."""
    x, n = breaches, days
    phat = x / n
    log_null = (n - x) * np.log(1 - p) + x * np.log(p)
    log_alt = (n - x) * np.log(1 - phat) + (x * np.log(phat) if x else 0.0)
    return float(stats.chi2.sf(-2 * (log_null - log_alt), df=1))


def christoffersen_independence(hits: np.ndarray) -> float:
    """p-value of 'a breach today is no more likely after a breach yesterday'. Small -> clustering."""
    prev, curr = hits[:-1], hits[1:]
    n00 = np.sum((prev == 0) & (curr == 0)); n01 = np.sum((prev == 0) & (curr == 1))
    n10 = np.sum((prev == 1) & (curr == 0)); n11 = np.sum((prev == 1) & (curr == 1))
    pi0 = n01 / (n00 + n01); pi1 = n11 / (n10 + n11) if (n10 + n11) else 0.0
    pi = (n01 + n11) / (n00 + n01 + n10 + n11)

    def ll(p, zeros, ones):
        return (zeros * np.log(1 - p) if zeros else 0.0) + (ones * np.log(p) if ones else 0.0)

    lr = -2 * (ll(pi, n00 + n10, n01 + n11) - ll(pi0, n00, n01) - ll(pi1, n10, n11))
    return float(stats.chi2.sf(lr, df=1))


def basel_zone(breaches_in_year: int) -> str:
    return "green" if breaches_in_year <= 4 else "yellow" if breaches_in_year <= 9 else "red"


# ---------------------------------------------------------------- report
def main() -> None:
    OUT.mkdir(exist_ok=True)
    returns = load_returns()
    var = rolling_var(returns).loc["1986-01-01":]     # whole calendar years only
    realised_loss = -returns.loc[var.index]
    hits = var.lt(realised_loss, axis=0).astype(int)      # 1 = loss bigger than forecast VaR

    days = len(var)
    lines = [
        "# VaR backtest — S&P 500",
        "",
        f"- Forecast days: **{days:,}** ({var.index[0].date()} to {var.index[-1].date()})",
        f"- One-day VaR at {CONFIDENCE:.0%}, rolling {WINDOW}-day window, no look-ahead",
        f"- Expected breaches at {1 - CONFIDENCE:.0%}: **{days * (1 - CONFIDENCE):,.1f}**",
        "",
        "| Model | Breaches | Breach rate | Kupiec p-value | Clustering p-value |",
        "|---|---|---|---|---|",
    ]
    for model in var.columns:
        x = int(hits[model].sum())
        lines.append(f"| {model} | {x:,} | {x / days:.2%} | {kupiec_pof(x, days):.4f} | "
                     f"{christoffersen_independence(hits[model].to_numpy()):.4f} |")

    by_year = hits.groupby(hits.index.year).sum()
    trading_days = hits.groupby(hits.index.year).size().rename("trading_days")
    table = by_year.join(trading_days)
    for model in var.columns:
        table[f"{model}_zone"] = table[model].map(basel_zone)
    table.to_csv(OUT / "breaches_by_year.csv")
    lines += ["", "## Worst years (historical-simulation breaches)", "",
              "| Year | Trading days | Historical | Parametric | Monte Carlo (t) |", "|---|---|---|---|---|"]
    # stable sort: years that tie on breaches stay in calendar order, so the table is the same on every machine
    for year, row in table.sort_values("historical", ascending=False, kind="stable").head(8).iterrows():
        lines.append(f"| {year} | {row.trading_days} | {row.historical} ({row.historical_zone}) | "
                     f"{row.parametric} ({row.parametric_zone}) | {row.monte_carlo} ({row.monte_carlo_zone}) |")

    bm = pd.Timestamp("1987-10-19")
    if bm in var.index:
        loss = realised_loss.loc[bm]
        lines += ["", "## Black Monday, 19 October 1987", "",
                  f"- Actual one-day loss: **{loss:.2%}** (${loss * PORTFOLIO:,.0f} on ${PORTFOLIO:,})"]
        for model in var.columns:
            v = var.loc[bm, model]
            lines.append(f"- {model} VaR that morning: {v:.2%} (${v * PORTFOLIO:,.0f}); "
                         f"the loss was **{loss / v:.1f}x** the forecast")
        window = returns.loc[:bm].iloc[-WINDOW - 1:-1]
        lines.append(f"- In standard deviations of the prior {WINDOW} days: **{loss / window.std(ddof=1):.1f}**")

    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    plot_crisis(returns, var, hits, "2007-06-01", "2009-06-30", OUT / "var_vs_losses_2007_2009.png")
    plot_by_year(table, OUT / "breaches_per_year.png")
    print("\n".join(lines))


def plot_crisis(returns, var, hits, start, end, path):
    r = returns.loc[start:end]; v = var.loc[start:end]; h = hits.loc[start:end, "historical"]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.bar(r.index, -r * 100, width=1.2, color=np.where(h.reindex(r.index, fill_value=0) == 1, "#d9534f", "#9aa5b1"))
    ax.plot(v.index, v["historical"] * 100, color="#f0a202", lw=2, label="Historical VaR 99%")
    ax.plot(v.index, v["parametric"] * 100, color="#1f8a70", lw=1.5, ls="--", label="Parametric VaR 99%")
    ax.set_ylabel("Daily loss, % (gains shown below zero)")
    ax.set_title("S&P 500 daily losses vs next-day VaR forecast, 2007-2009 (red = breach)")
    ax.legend(loc="upper left"); ax.axhline(0, color="black", lw=0.6)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def plot_by_year(table, path):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(table.index, table["historical"], color="#34495e", label="Historical VaR breaches")
    ax.axhline(2.5, color="#1f8a70", ls="--", label="Expected at 99% (2.5 a year)")
    ax.axhline(10, color="#d9534f", ls=":", label="Basel red zone (10+)")
    ax.set_title("S&P 500: 99% VaR breaches per year, historical simulation, 250-day window")
    ax.legend(loc="upper left"); ax.set_ylabel("Breaches")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


if __name__ == "__main__":
    main()
