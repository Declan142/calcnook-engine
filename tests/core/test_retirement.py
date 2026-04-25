"""Tests for retirement planning functions."""

import pytest

from calcnook.core import retirement


# ---------------------------------------------------------------------------
# corpus_needed
# ---------------------------------------------------------------------------

def test_corpus_needed_basic():
    # 50k/yr for 30y retirement, 7% return, 6% inflation
    # real rate = (1.07/1.06) - 1 ≈ 0.009434
    result = retirement.corpus_needed(50_000, 30, 0.07, 0.06)
    assert result.corpus_needed > 0
    # Should be roughly between 1M and 2M for these inputs
    assert 1_000_000 < result.corpus_needed < 2_000_000


def test_corpus_needed_zero_real_rate():
    # When return == inflation, real rate = 0 -> corpus = expense * years
    result = retirement.corpus_needed(50_000, 30, 0.05, 0.05)
    assert result.corpus_needed == pytest.approx(50_000 * 30, rel=1e-6)


def test_corpus_needed_high_return():
    # Higher return -> less corpus needed
    r_low = retirement.corpus_needed(50_000, 30, 0.06, 0.03)
    r_high = retirement.corpus_needed(50_000, 30, 0.10, 0.03)
    assert r_high.corpus_needed < r_low.corpus_needed


def test_corpus_needed_invalid_expense():
    with pytest.raises(ValueError, match="annual_expense"):
        retirement.corpus_needed(0, 30, 0.07, 0.06)


def test_corpus_needed_invalid_years():
    with pytest.raises(ValueError, match="years_in_retirement"):
        retirement.corpus_needed(50_000, 0, 0.07, 0.06)


def test_corpus_needed_to_dict():
    result = retirement.corpus_needed(50_000, 30, 0.07, 0.06)
    d = result.to_dict()
    assert "corpus_needed" in d
    assert "annual_expense" in d
    assert d["annual_expense"] == 50_000


# ---------------------------------------------------------------------------
# monthly_contribution_for
# ---------------------------------------------------------------------------

def test_monthly_contribution_basic():
    # 1 Cr target in 20y at 12% annual, no current savings
    result = retirement.monthly_contribution_for(10_000_000, 20, 0.12)
    assert result.monthly_contribution > 0
    # Rough sanity: ~10k/month for 10M corpus in 20y at 12%
    assert 8_000 < result.monthly_contribution < 15_000


def test_monthly_contribution_zero_rate():
    # 0% return: monthly = corpus / n
    result = retirement.monthly_contribution_for(120_000, 10, 0.0)
    assert result.monthly_contribution == pytest.approx(120_000 / 120, rel=1e-6)


def test_monthly_contribution_existing_savings_reduces_amount():
    r_no_savings = retirement.monthly_contribution_for(10_000_000, 20, 0.12, 0)
    r_with_savings = retirement.monthly_contribution_for(10_000_000, 20, 0.12, 500_000)
    assert r_with_savings.monthly_contribution < r_no_savings.monthly_contribution


def test_monthly_contribution_savings_exceed_target():
    # If existing savings already exceed corpus, contribution should be 0
    result = retirement.monthly_contribution_for(100_000, 30, 0.12, 200_000)
    assert result.monthly_contribution == 0.0


def test_monthly_contribution_invalid_target():
    with pytest.raises(ValueError, match="target_corpus"):
        retirement.monthly_contribution_for(0, 20, 0.12)


def test_monthly_contribution_invalid_years():
    with pytest.raises(ValueError, match="years_to_retirement"):
        retirement.monthly_contribution_for(1_000_000, 0, 0.12)


def test_monthly_contribution_to_dict():
    result = retirement.monthly_contribution_for(10_000_000, 20, 0.12)
    d = result.to_dict()
    assert "monthly_contribution" in d
    assert "target_corpus" in d


# ---------------------------------------------------------------------------
# safe_withdrawal
# ---------------------------------------------------------------------------

def test_safe_withdrawal_4pct_1M():
    result = retirement.safe_withdrawal(1_000_000)
    assert result.annual_withdrawal == pytest.approx(40_000.0, rel=1e-9)
    assert result.monthly_withdrawal == pytest.approx(40_000 / 12, rel=1e-9)


def test_safe_withdrawal_custom_rate():
    result = retirement.safe_withdrawal(1_000_000, withdrawal_rate=0.03)
    assert result.annual_withdrawal == pytest.approx(30_000.0, rel=1e-9)


def test_safe_withdrawal_invalid_corpus():
    with pytest.raises(ValueError, match="corpus"):
        retirement.safe_withdrawal(0)


def test_safe_withdrawal_invalid_rate_zero():
    with pytest.raises(ValueError, match="withdrawal_rate"):
        retirement.safe_withdrawal(1_000_000, withdrawal_rate=0.0)


def test_safe_withdrawal_invalid_rate_over_one():
    with pytest.raises(ValueError, match="withdrawal_rate"):
        retirement.safe_withdrawal(1_000_000, withdrawal_rate=1.5)


def test_safe_withdrawal_to_dict():
    result = retirement.safe_withdrawal(1_000_000)
    d = result.to_dict()
    assert "annual_withdrawal" in d
    assert "monthly_withdrawal" in d
    assert d["corpus"] == 1_000_000
    assert d["withdrawal_rate"] == 0.04
