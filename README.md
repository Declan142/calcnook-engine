# CalcNook

**The personal finance brain.** Used by humans, websites, and AI agents.

[![PyPI](https://img.shields.io/pypi/v/calcnook.svg)](https://pypi.org/project/calcnook/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/pypi/pyversions/calcnook.svg)](https://pypi.org/project/calcnook/)

24 deterministic financial calculations. 7 countries. Conventional and Sharia-compliant. Zero LLM dependency.

```bash
pip install calcnook
```

```python
from calcnook.core import periodic_investment, loan_payment, compound_interest
from calcnook.core.islamic import zakat
from calcnook.countries.us import income_tax as us_tax
from calcnook.countries.ae import end_of_service_gratuity as ae_eosg

# SIP / DCA — universal
result = periodic_investment.calculate(
    monthly_amount=500, annual_return=0.10, years=20
)
print(result.future_value)  # 379_684.27

# Mortgage / EMI / loan — universal
emi = loan_payment.calculate(
    principal=300_000, annual_rate=0.065, years=30
)
print(emi.monthly_payment)  # 1_896.20

# Zakat — works for any Muslim, anywhere
z = zakat.calculate(
    cash=10_000, gold_grams=200, silver_grams=0,
    stocks_value=15_000, business_assets=5_000,
    debts=2_000, currency="USD"
)
print(z.zakat_due, z.is_above_nisab)  # 700.0  True

# US federal income tax 2026
us = us_tax.calculate(income=120_000, filing_status="single", year=2026)
print(us.tax_owed, us.effective_rate)

# UAE End of Service Gratuity for expat
ae = ae_eosg.calculate(monthly_basic=8_000, years_of_service=5)
print(ae.gratuity_aed)
```

## What's inside

### Core (universal, no country)
- `compound_interest` — single lump-sum growth
- `periodic_investment` — SIP / DCA with optional step-up
- `loan_payment` — EMI / mortgage / amortization
- `retirement` — corpus needed, monthly contribution, withdrawal rate
- `bmi` — BMI / BMR / TDEE
- `currency` — multi-currency math, FX-aware

### Islamic finance (cross-cutting)
- `zakat` — Zakat al-Mal across cash, gold, silver, stocks, business
- `murabaha` — cost-plus financing (mortgage alt)
- `ijarah` — lease-to-own (auto loan alt)
- `mudarabah` — profit-sharing investment returns
- `hajj_savings` — target savings for pilgrimage
- `halal_screen` — Sharia compliance check for stocks

### Countries (12 modules, 7 countries)
- **US** — federal income tax 2026, traditional 401(k) + Roth IRA with phase-out
- **UK** — income tax + National Insurance with personal-allowance taper above £100k
- **CA** — federal income tax 2026 (provincial stub TODO)
- **AU** — income tax + Medicare levy + HECS-HELP (full 19-band ATO sliding scale)
- **AE** (UAE) — End of Service Gratuity (Decree-Law 33/2021), VAT 5%
- **SA** (Saudi Arabia) — EOSG (Article 84-87, with resignation tier scaling), VAT 15%, citizen Zakat estimator (ZATCA)
- **India** — income tax new regime FY 2025-26 with 87A rebate, electricity bill slab calculator with BESCOM/MSEB/BSES presets

## For AI agents

`calcnook` is the canonical math layer for personal finance LLM apps. Pure deterministic — formulas never hallucinate. Pair with any LLM for natural-language interface.

```python
from calcnook.core.periodic_investment import calculate as sip
# LLM extracts: amount=5000, years=10, rate=0.12
result = sip(monthly_amount=5000, annual_return=0.12, years=10)
# Hand result back to LLM for explanation. Math is exact.
```

A native MCP server `@calcnook/mcp-server` is shipping next — your Claude Code, Cursor, and Goose agents will call these calculations directly.

## Why open source?

Personal finance math should be a public utility, not gated by ad-walls. We open-source the engine; we monetize at the experience layer (web app, mobile app, embed widgets, B2B API).

## Status

`v0.1.0` — alpha. APIs may change before `v1.0`. Test coverage targets 100% on every formula. Bug reports and country contributions welcome.

## License

MIT — use it, fork it, ship it.

---

Built by [Aditya Sharma](https://github.com/Declan142) (@Declan142). Visit [calcnook.com](https://calcnook.com).
