"""The three VaR models, checked on toy windows whose answers can be worked out by hand."""
import math

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import var_backtest as vb

Z_99 = 2.3263478740408408  # 99% quantile of the standard normal, written out rather than read from scipy


def returns_series(n, seed=11, start="2000-01-03"):
    r = np.random.default_rng(seed).normal(0.0003, 0.01, n)
    return pd.Series(r, index=pd.bdate_range(start, periods=n), name="return")


@pytest.fixture
def few_draws(monkeypatch):
    """Fewer Monte Carlo draws so the rolling loops run fast. The formulas are unchanged."""
    monkeypatch.setattr(vb, "MC_DRAWS", 500)


def test_settings_are_the_ones_the_write_up_states():
    # 99% one-day VaR, 250-day window, 10,000 draws from a t with 4 degrees of freedom, seed 7
    assert (vb.CONFIDENCE, vb.WINDOW, vb.MC_DRAWS, vb.MC_DF, vb.SEED) == (0.99, 250, 10_000, 4, 7)


# ---------------------------------------------------------------- historical
def test_historical_var_on_a_linear_ramp():
    # 250 returns evenly spaced from -5% to +5%: the 1% quantile is -5% + 1% x 10% = -4.9%
    window = np.linspace(-0.05, 0.05, vb.WINDOW)
    assert vb.var_historical(window) == pytest.approx(0.049, abs=1e-12)


def test_historical_var_inside_a_block_of_equal_tail_losses():
    # ten -8% days among 250: the 1% quantile sits between the 3rd and 4th worst, both -8%
    window = np.r_[np.full(10, -0.08), np.full(240, 0.01)]
    assert vb.var_historical(window) == pytest.approx(0.08)


def test_historical_var_ignores_the_order_of_days():
    rng = np.random.default_rng(1)
    window = rng.normal(0, 0.01, vb.WINDOW)
    assert vb.var_historical(rng.permutation(window)) == vb.var_historical(window)


def test_historical_var_follows_a_shift_and_a_rescale():
    window = np.random.default_rng(2).normal(0, 0.01, vb.WINDOW)
    base = vb.var_historical(window)
    assert vb.var_historical(window + 0.002) == pytest.approx(base - 0.002)
    assert vb.var_historical(window * 3) == pytest.approx(base * 3)


# ---------------------------------------------------------------- parametric
def test_parametric_var_known_answer():
    # half +1%, half -1%: mean 0 and sample sd (n-1 divisor) = 1% x sqrt(250/249), so VaR = 0.023310...
    window = np.array([0.01, -0.01] * 125)
    assert vb.var_parametric(window) == pytest.approx(Z_99 * 0.01 * math.sqrt(250 / 249), rel=1e-12)


def test_parametric_var_is_2326_standard_deviations():
    window = np.random.default_rng(3).normal(0, 0.01, vb.WINDOW)
    assert vb.var_parametric(window) / window.std(ddof=1) == pytest.approx(2.326, abs=5e-4)


def test_parametric_var_ignores_the_mean_and_follows_a_rescale():
    window = np.random.default_rng(3).normal(0, 0.01, vb.WINDOW)
    base = vb.var_parametric(window)
    assert vb.var_parametric(window + 0.01) == pytest.approx(base)   # method uses the sd only
    assert vb.var_parametric(window * 4) == pytest.approx(base * 4)


# ---------------------------------------------------------------- Monte Carlo
def test_monte_carlo_var_is_reproducible_with_a_fixed_seed():
    window = np.random.default_rng(3).normal(0, 0.01, vb.WINDOW)
    first = vb.var_monte_carlo(window, np.random.default_rng(vb.SEED))
    again = vb.var_monte_carlo(window, np.random.default_rng(vb.SEED))
    other_seed = vb.var_monte_carlo(window, np.random.default_rng(vb.SEED + 1))
    assert first == again
    assert first != other_seed


def test_monte_carlo_var_converges_to_the_rescaled_t_quantile(monkeypatch):
    # With very many draws the answer is sd x (99% quantile of t4, rescaled to variance 1) = 2.6495 x sd.
    # Without the rescale it would be 3.747 x sd, so this pins down the sqrt((df-2)/df) factor too.
    monkeypatch.setattr(vb, "MC_DRAWS", 2_000_000)
    window = np.random.default_rng(4).normal(0, 0.01, vb.WINDOW)
    expected = window.std(ddof=1) * stats.t.ppf(0.99, 4) * math.sqrt(0.5)
    assert vb.var_monte_carlo(window, np.random.default_rng(vb.SEED)) == pytest.approx(expected, rel=0.01)


def test_monte_carlo_var_follows_a_rescale_of_the_window():
    window = np.random.default_rng(5).normal(0, 0.01, vb.WINDOW)
    base = vb.var_monte_carlo(window, np.random.default_rng(vb.SEED))
    assert vb.var_monte_carlo(window * 2, np.random.default_rng(vb.SEED)) == pytest.approx(base * 2)


# ---------------------------------------------------------------- the rolling forecast
def test_rolling_var_first_forecast_uses_exactly_the_first_250_returns(few_draws):
    returns = returns_series(300)
    var = vb.rolling_var(returns)
    first = returns.to_numpy()[: vb.WINDOW]
    assert len(var) == 300 - vb.WINDOW
    assert var.index[0] == returns.index[vb.WINDOW]            # the first forecast is for day 251
    assert var["historical"].iloc[0] == pytest.approx(vb.var_historical(first))
    assert var["parametric"].iloc[0] == pytest.approx(vb.var_parametric(first))
    assert var["monte_carlo"].iloc[0] == pytest.approx(vb.var_monte_carlo(first, np.random.default_rng(vb.SEED)))


def test_rolling_var_has_no_look_ahead(few_draws):
    returns = returns_series(400)
    t = 320
    shocked = returns.copy()
    shocked.iloc[t] = -0.30                                    # a crash on day t
    a, b = vb.rolling_var(returns), vb.rolling_var(shocked)
    up_to_t = a.index <= returns.index[t]
    # no forecast made on or before day t may notice it (day t's own forecast uses days t-250 .. t-1) ...
    pd.testing.assert_frame_equal(a[up_to_t], b[up_to_t], check_exact=True)
    # ... and the next day's forecast must, since day t is now inside its window
    assert (a.loc[returns.index[t + 1]] != b.loc[returns.index[t + 1]]).all()


def test_rolling_var_is_reproducible(few_draws):
    returns = returns_series(300)
    pd.testing.assert_frame_equal(vb.rolling_var(returns), vb.rolling_var(returns), check_exact=True)


def test_the_seed_moves_only_the_monte_carlo_column(few_draws, monkeypatch):
    returns = returns_series(300)
    base = vb.rolling_var(returns)
    monkeypatch.setattr(vb, "SEED", vb.SEED + 1)
    other = vb.rolling_var(returns)
    pd.testing.assert_series_equal(base["historical"], other["historical"], check_exact=True)
    pd.testing.assert_series_equal(base["parametric"], other["parametric"], check_exact=True)
    assert not np.allclose(base["monte_carlo"], other["monte_carlo"])
