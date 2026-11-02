"""A full run of main() on made-up prices, writing into a temporary folder (never into results/)."""
import re

import numpy as np
import pandas as pd
import pytest

import var_backtest as vb

MODELS = ["historical", "parametric", "monte_carlo"]


def write_made_up_prices(path):
    """Business days 1985-2010 so that the 1987 and 2007-2009 sections of the report exist."""
    dates = pd.bdate_range("1985-01-02", "2010-12-31")
    log_returns = np.random.default_rng(123).normal(0.0003, 0.011, len(dates))
    log_returns[dates.get_loc(pd.Timestamp("1987-10-19"))] = -0.20          # a Black Monday
    close = 100 * np.exp(np.cumsum(log_returns))
    pd.DataFrame({"date": dates, "close": close, "check": "agree_3"}).to_csv(path, index=False)


def test_main_runs_end_to_end_and_its_outputs_agree_with_each_other(tmp_path, monkeypatch, capsys):
    data, out = tmp_path / "close.csv", tmp_path / "results"
    write_made_up_prices(data)
    monkeypatch.setattr(vb, "DATA", data)
    monkeypatch.setattr(vb, "OUT", out)
    monkeypatch.setattr(vb, "MC_DRAWS", 300)           # fewer draws to keep the test quick

    vb.main()

    for name in ["summary.md", "breaches_by_year.csv", "breaches_per_year.png", "var_vs_losses_2007_2009.png"]:
        assert (out / name).stat().st_size > 0, name
    for name in ["breaches_per_year.png", "var_vs_losses_2007_2009.png"]:
        assert (out / name).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", name

    summary = (out / "summary.md").read_text()
    by_year = pd.read_csv(out / "breaches_by_year.csv", index_col=0)
    assert list(by_year.index) == list(range(1986, 2011))
    assert f"Forecast days: **{int(by_year['trading_days'].sum()):,}**" in summary
    for model in MODELS:
        assert f"| {model} | {int(by_year[model].sum()):,} |" in summary
        assert (by_year[f"{model}_zone"] == by_year[model].map(vb.basel_zone)).all()
    assert "## Black Monday, 19 October 1987" in summary
    assert capsys.readouterr().out.strip() == summary.strip()           # what it prints is what it saves
    assert "nan" not in summary.lower()


# Historical-simulation breaches per year, 1986 to 2026, copied from results/breaches_by_year.csv.
# Four years (1994, 1996, 1997, 2018) tie on 7 breaches, right at the cut-off of the top-8 table.
HISTORICAL_BREACHES = dict(zip(range(1986, 2027), [
    9, 6, 1, 4, 4, 2, 0, 2, 7, 1, 7, 7, 4, 1, 6, 3, 5, 1, 2, 3, 4, 10, 13, 0, 3, 6, 1, 2, 4, 6, 2, 3, 7, 1,
    8, 1, 10, 0, 6, 4, 1]))


def test_worst_years_table_does_not_depend_on_the_sort_implementation(tmp_path, monkeypatch):
    """Years that tie on breaches must come out in calendar order, so the table is the same on every machine.
    (The default pandas sort is not stable; on a clean install it showed 2018 where the committed table has 1996.)"""
    days, losses = [], []
    for year, breaches in HISTORICAL_BREACHES.items():
        days.append(pd.bdate_range(f"{year}-01-02", periods=252))
        r = np.full(252, 0.001)
        r[:breaches] = -0.05                                   # these days lose 5%, more than the 2% VaR below
        losses.append(r)
    returns = pd.Series(np.concatenate(losses), index=days[0].append(days[1:]), name="return")
    flat_var = pd.DataFrame(0.02, index=returns.index, columns=MODELS)
    monkeypatch.setattr(vb, "load_returns", lambda: returns)
    monkeypatch.setattr(vb, "rolling_var", lambda _returns: flat_var)
    monkeypatch.setattr(vb, "plot_crisis", lambda *args, **kwargs: None)
    monkeypatch.setattr(vb, "plot_by_year", lambda *args, **kwargs: None)
    monkeypatch.setattr(vb, "OUT", tmp_path)

    vb.main()

    summary = (tmp_path / "summary.md").read_text()
    worst = summary.split("## Worst years")[1].split("## Black Monday")[0]
    shown = [int(year) for year in re.findall(r"^\| (\d{4}) \|", worst, flags=re.M)]
    expected = sorted(HISTORICAL_BREACHES, key=lambda year: (-HISTORICAL_BREACHES[year], year))[:8]
    assert expected == [2008, 2007, 2022, 1986, 2020, 1994, 1996, 1997]
    assert shown == expected
