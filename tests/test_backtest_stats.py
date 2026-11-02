"""Kupiec and Christoffersen backtest statistics and the Basel zones, on cases with known answers."""
import math
import warnings

import numpy as np
import pytest
from scipy import stats

import var_backtest as vb


def chi2_1_sf(x):
    """Survival function of a chi-square with 1 degree of freedom, from the standard library only."""
    return math.erfc(math.sqrt(x / 2))


# ---------------------------------------------------------------- Kupiec proportion of failures
@pytest.mark.parametrize("breaches, days", [(10, 1000), (25, 2500), (1, 100)])
def test_kupiec_p_value_is_one_when_breaches_equal_the_expected_number(breaches, days):
    assert vb.kupiec_pof(breaches, days) == pytest.approx(1.0)


def test_kupiec_with_no_breaches_has_a_closed_form():
    # x = 0 gives LR = -2 n ln(1 - p) = 5.0252 for n = 250, p = 1%, so p-value = 0.02498
    lr = -2 * 250 * math.log(0.99)
    assert vb.kupiec_pof(0, 250) == pytest.approx(chi2_1_sf(lr), rel=1e-9)
    assert vb.kupiec_pof(0, 250) == pytest.approx(0.02498, abs=1e-5)


def test_kupiec_flips_between_six_and_seven_breaches_in_255_days():
    # worked by hand: LR(6) = 3.415 < 3.841 <= LR(7) = 5.316, the 5% cut-off of a chi-square(1)
    assert vb.kupiec_pof(6, 255) == pytest.approx(0.0646, abs=5e-4)
    assert vb.kupiec_pof(7, 255) == pytest.approx(0.0211, abs=5e-4)


@pytest.mark.parametrize("breaches, days", [(0, 250), (3, 250), (10, 250), (4, 1000), (167, 10_255), (224, 10_255)])
def test_kupiec_matches_a_binomial_likelihood_ratio(breaches, days):
    # same test written through scipy's binomial: LR = -2 ln [ L(p = 1%) / L(p = x/n) ]
    lr = -2 * (stats.binom.logpmf(breaches, days, 0.01) - stats.binom.logpmf(breaches, days, breaches / days))
    assert vb.kupiec_pof(breaches, days) == pytest.approx(stats.chi2.sf(lr, 1), rel=1e-6, abs=1e-12)


@pytest.mark.parametrize("breaches", [167, 224, 154])
def test_kupiec_reproduces_the_summary_p_values_from_the_breach_counts(breaches):
    # results/summary.md: 10,255 forecast days; 167 / 224 / 154 breaches; every Kupiec p-value prints as 0.0000
    assert f"{vb.kupiec_pof(breaches, 10_255):.4f}" == "0.0000"


# ---------------------------------------------------------------- Christoffersen independence
def transition_table(hits):
    prev, curr = hits[:-1], hits[1:]
    return np.array([[np.sum((prev == a) & (curr == b)) for b in (0, 1)] for a in (0, 1)])


def g_test_p(hits):
    """The same statistic as a likelihood-ratio (G) test of independence on the 2x2 table of
    yesterday's breach vs today's breach, from scipy's contingency-table routine."""
    return stats.chi2_contingency(transition_table(hits), correction=False, lambda_="log-likelihood").pvalue


def markov_hits(n, p_after_calm, p_after_breach, seed):
    rng = np.random.default_rng(seed)
    hits = np.zeros(n, dtype=int)
    for i in range(1, n):
        hits[i] = rng.random() < (p_after_breach if hits[i - 1] else p_after_calm)
    return hits


def test_christoffersen_gives_one_when_breaches_do_not_depend_on_yesterday():
    # transitions: 0>0 x4, 0>1 x2, 1>0 x2, 1>1 x1, so P(breach | calm) = 2/6 = P(breach | breach) = 1/3
    hits = np.array([0, 0, 0, 0, 1, 1, 0, 1, 0, 0])
    assert transition_table(hits).tolist() == [[4, 2], [2, 1]]
    assert vb.christoffersen_independence(hits) == pytest.approx(1.0)


def test_christoffersen_with_no_breaches_is_one_and_warning_free():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert vb.christoffersen_independence(np.zeros(250, dtype=int)) == 1.0


def test_same_breach_count_clustered_or_spread_out():
    clustered = np.zeros(250, dtype=int)
    clustered[100:105] = 1                                      # five breaches in a row
    spread = np.zeros(250, dtype=int)
    spread[[25, 75, 125, 175, 225]] = 1                         # five breaches, far apart
    # Kupiec only sees the count, so it cannot tell them apart ...
    assert vb.kupiec_pof(int(clustered.sum()), 250) == vb.kupiec_pof(int(spread.sum()), 250)
    # ... Christoffersen can (worked by hand: LR = 30.98 vs 0.20)
    assert vb.christoffersen_independence(clustered) == pytest.approx(chi2_1_sf(30.98), rel=1e-2)
    assert vb.christoffersen_independence(spread) == pytest.approx(chi2_1_sf(0.2006), rel=1e-2)


@pytest.mark.parametrize("p_after_calm, p_after_breach, seed",
                         [(0.01, 0.01, 1), (0.01, 0.30, 2), (0.02, 0.05, 3), (0.01, 0.0, 4)])
def test_christoffersen_matches_the_contingency_table_g_test(p_after_calm, p_after_breach, seed):
    hits = markov_hits(3000, p_after_calm, p_after_breach, seed)
    assert vb.christoffersen_independence(hits) == pytest.approx(g_test_p(hits), rel=1e-9)


# ---------------------------------------------------------------- Basel traffic light
@pytest.mark.parametrize("breaches, zone", [(0, "green"), (4, "green"), (5, "yellow"), (9, "yellow"),
                                            (10, "red"), (13, "red")])
def test_basel_zone_boundaries(breaches, zone):
    assert vb.basel_zone(breaches) == zone
