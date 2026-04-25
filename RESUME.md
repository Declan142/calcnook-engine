# RESUME — calcnook-engine

**30-second pickup:** Open-source Python package implementing 24 deterministic financial calculations across 7 countries + Islamic finance module. The math layer for the calcnook.com global relaunch. **v0.1.1 LIVE on PyPI** as `pip install calcnook`.

## Live status

- **PyPI:** https://pypi.org/project/calcnook/0.1.1/ — globally installable (v0.1.1 patch shipped 2026-04-25)
- **GitHub:** https://github.com/Declan142/calcnook-engine — public, MIT, main branch
- **Latest release:** https://github.com/Declan142/calcnook-engine/releases/tag/v0.1.1
- **Trusted publisher:** configured + battle-tested (v0.1.1 auto-published in 25s via GitHub Release)
- **Tests:** 307 passing on Python 3.10/3.11/3.12/3.13
- **Dependencies:** zero (pure stdlib)

## What ships in v0.1.0

| Module | What it does |
|---|---|
| `calcnook.core.compound_interest` | Lump-sum growth |
| `calcnook.core.periodic_investment` | SIP / DCA + step-up |
| `calcnook.core.loan_payment` | EMI / mortgage / amortization |
| `calcnook.core.retirement` | Corpus needed / contribution / withdrawal |
| `calcnook.core.bmi` | BMI / BMR / TDEE |
| `calcnook.core.currency` | Convert + format + lakh/crore |
| `calcnook.core.islamic.zakat` | Zakat al-Mal across all asset classes |
| `calcnook.core.islamic.murabaha` | Cost-plus financing (Sharia mortgage alt) |
| `calcnook.core.islamic.ijarah` | Lease-to-own (Sharia auto-loan alt) |
| `calcnook.core.islamic.mudarabah` | Profit-sharing investment |
| `calcnook.core.islamic.hajj_savings` | Target-based pilgrimage savings |
| `calcnook.core.islamic.halal_screen` | AAOIFI Sharia stock screening |
| `calcnook.countries.us.income_tax` | US federal 2026 brackets, 4 filing statuses |
| `calcnook.countries.us.retirement_accounts` | Traditional 401(k) + Roth IRA |
| `calcnook.countries.uk.income_tax` | UK + NI with personal-allowance taper |
| `calcnook.countries.ca.income_tax` | Canada federal (provincial TODO) |
| `calcnook.countries.au.income_tax` | Australia + Medicare + HECS-HELP |
| `calcnook.countries.ae.end_of_service_gratuity` | UAE EOSG (Decree-Law 33/2021) |
| `calcnook.countries.ae.vat` | UAE VAT 5% |
| `calcnook.countries.sa.end_of_service_gratuity` | Saudi EOSG (Article 84-87, resignation tiers) |
| `calcnook.countries.sa.vat` | Saudi VAT 15% |
| `calcnook.countries.sa.zakat_citizen` | Saudi citizen ZATCA Zakat estimator |
| `calcnook.countries.india.income_tax` | India new regime FY 25-26 + 87A rebate |
| `calcnook.countries.india.electricity_bill` | Slab calculator + BESCOM/MSEB/BSES presets |

## Quick verify

```bash
pip install calcnook
python -c "
from calcnook.core.periodic_investment import calculate
print(calculate(monthly_amount=5000, annual_return=0.12, years=10).future_value)
"
# 1161695.38
```

## Open threads

- **Future versions** — bump `version` in `pyproject.toml` and `src/calcnook/__init__.py`, commit, `git tag vX.Y.Z && git push origin main vX.Y.Z && gh release create vX.Y.Z` — workflow auto-publishes via trusted publisher (validated end-to-end on v0.1.1, 25s build)
- **Country expansion** — Phase 1 covers 7 countries. Add Egypt (EG), Pakistan (PK), Indonesia (ID), Singapore (SG), Germany (DE) in v0.2.0+
- **i18n** — `src/calcnook/i18n/{en,ar}` skeleton exists. Wire up Hindi/Spanish/Arabic display strings when web app is ready
- **Provincial Canada** — `countries/ca/income_tax.py` returns 0 provincial tax (documented TODO)

## Open issues / known limitations

- pyproject.toml `description` still says "22 calculations" but actual count is 24 — fold into next patch (v0.1.2) or wait until country expansion bumps to 0.2.0
- Saudi `zakat_citizen` is a SIMPLIFIED estimator — real ZATCA filing is far more complex (adjusted equity etc.) — caller should consult ZATCA
- GitHub Actions still on Node 20 (deprecation warning on every run; actions removed Sep 2026) — bump `actions/checkout@v4 → v5` and `actions/setup-python@v5 → v6` when convenient

## How to run tests

```bash
cd ~/repos/calcnook-engine
pip install --break-system-packages -e ".[dev]"
python3 -m pytest -q
# 307 passed
```

## Repos sister to this one

- **MCP server** — `~/repos/calcnook-mcp-server` → https://github.com/Declan142/calcnook-mcp-server (also LIVE on PyPI as `calcnook-mcp` v0.1.0)
- **Web app** — `Declan142/calcnook` (Next.js, current — pending W3 rebuild)

## Project context

Full project doc: `~/.claude/atlas/projects/active/calcnook-v2-global-relaunch.md`

Atlas memory pointer: `~/.claude/projects/-home-aditya/memory/project_calcnook_v2_global_relaunch.md`

PyPI vault: `~/.claude/vault/pypi.md` (chmod 600)
