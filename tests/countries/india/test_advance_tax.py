"""Tests for India Advance Tax — Section 211 instalment schedule."""

import pytest

from calcnook.countries.india import advance_tax


def test_q1_due_in_april():
    """Apr 1 → Q1 (Jun 15) is the next due."""
    r = advance_tax.calculate(
        annual_income=2_500_000,
        regime="new",
        as_of_date="2025-04-01",
    )
    assert r.current_quarter == "Q1"
    assert r.next_due_date == "2025-06-15"
    # 15% cumulative
    assert r.next_installment_required_cumulative == pytest.approx(0.15 * r.total_tax_estimated, rel=1e-4)


def test_q2_due_in_august():
    """Aug 1 → Q2 (Sep 15) is the next due (45% cumulative)."""
    r = advance_tax.calculate(
        annual_income=2_500_000,
        regime="new",
        as_of_date="2025-08-01",
    )
    assert r.current_quarter == "Q2"
    assert r.next_due_date == "2025-09-15"
    assert r.next_installment_required_cumulative == pytest.approx(0.45 * r.total_tax_estimated, rel=1e-4)


def test_q3_due_in_november():
    """Nov 1 → Q3 (Dec 15) next due (75%)."""
    r = advance_tax.calculate(
        annual_income=2_500_000,
        regime="new",
        as_of_date="2025-11-01",
    )
    assert r.current_quarter == "Q3"
    assert r.next_due_date == "2025-12-15"
    assert r.next_installment_required_cumulative == pytest.approx(0.75 * r.total_tax_estimated, rel=1e-4)


def test_q4_due_in_february():
    """Feb 1 → Q4 (Mar 15 next CY) next due (100%)."""
    r = advance_tax.calculate(
        annual_income=2_500_000,
        regime="new",
        as_of_date="2026-02-01",
    )
    assert r.current_quarter == "Q4"
    # FY 2025-26 → Mar 15, 2026
    assert r.next_due_date == "2026-03-15"
    assert r.next_installment_required_cumulative == pytest.approx(r.total_tax_estimated, rel=1e-4)


def test_paid_so_far_reduces_due():
    r = advance_tax.calculate(
        annual_income=2_500_000,
        regime="new",
        paid_so_far=50_000,
        as_of_date="2025-08-01",
    )
    cumulative_required = 0.45 * r.total_tax_estimated
    expected_due_now = max(0.0, cumulative_required - 50_000)
    assert r.next_installment_due_now == pytest.approx(expected_due_now, rel=1e-3)


def test_low_income_no_advance_tax_needed():
    """≤ ₹10K total tax → Sec 208 says no advance tax due."""
    # 5L gross under new regime → 0 tax due to 87A
    r = advance_tax.calculate(annual_income=500_000, regime="new", as_of_date="2025-04-01")
    assert r.total_tax_estimated == 0.0
    assert r.note is not None and "Sec 208" in r.note


def test_all_four_installments_listed():
    r = advance_tax.calculate(annual_income=2_500_000, as_of_date="2025-04-01")
    assert len(r.all_installments) == 4
    quarters = [i.quarter for i in r.all_installments]
    assert quarters == ["Q1", "Q2", "Q3", "Q4"]
