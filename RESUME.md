# RESUME — calcnook-engine

**30-second pickup:** Open-source Python package implementing 22 financial calculations across 7 countries + Islamic finance module. The math layer for the calcnook.com global relaunch. MIT, public.

## Status (2026-04-25)

- Foundation scaffolded: pyproject.toml, README, directory tree, 2 template modules (compound_interest, zakat) with 21 tests passing.
- 3 Sonnet 4.6 agents currently building remaining 20 modules in parallel.
- Not yet published to PyPI — need API token.

## What ships in v0.1.0

- `core/` — compound_interest, periodic_investment (SIP/DCA), loan_payment (EMI/mortgage), retirement, bmi, currency
- `core/islamic/` — zakat, murabaha, ijarah, mudarabah, hajj_savings, halal_screen
- `countries/` — us, uk, ca, au, ae (UAE), sa (Saudi Arabia), india (renamed from `in/` due to Python keyword)

## Open threads

1. **PyPI publish** — needs token from pypi.org. Aditya to create, then `python3 -m build && python3 -m twine upload dist/*`.
2. **Sonnet agent results** — 3 agents in flight, await completion + quality review.
3. **MCP server** — `calcnook-mcp-server` repo not yet created. Phase 1 W4.
4. **Web app rebuild** — `Declan142/calcnook` (Next.js, current) needs full rewrite to single-input UI. Phase 1 W3.

## How to run tests

```bash
cd ~/repos/calcnook-engine
pip install --break-system-packages -e ".[dev]"
python3 -m pytest -q
```

## Repo

https://github.com/Declan142/calcnook-engine — public, MIT, main branch.

## Project context

Full project doc: `~/.claude/atlas/projects/active/calcnook-v2-global-relaunch.md`
