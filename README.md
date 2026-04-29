# CodexTrading

CodexTrading is a production-oriented Python trading application scaffold for Interactive Brokers market data workflows. This repository starts with a reliable `ibapi` + `asyncio` market data client for AAPL and packages the broader trading rules from [`trading_rules.docx`](C:\Users\Girish\Desktop\CodexTrading\trading_rules.docx) into a maintainable project structure that can grow into a full rules engine, execution service, and risk platform.

## Current Scope

- Stream AAPL market data from IB TWS or IB Gateway using `ibapi`
- Use `asyncio`, `argparse`, `dataclasses`, `Optional`, and `Set`
- Provide a clean package layout, tests, and CI/CD automation
- Capture product context, architecture direction, and tracked work in repository docs
- Preserve cross-session project context with semantic session memory

## Trading Rules Summary

The source rules document defines a large rule set that goes beyond price polling. The current application implements market data acquisition first so the rest of the platform can be built on a stable feed.

### Rule Categories

- Opening imbalance checks around `06:30:00-06:30:59 PST`
- One-minute opening range breakout checks around `06:31:00-06:31:02 PST`
- Momentum confirmation using the last 600 ticks
- Market context filters such as VWAP, breadth, sector confirmation, and VIX
- Volume and liquidity filters such as RVOL, ATR, dollar volume, and spread control
- Candle structure, order flow, bid/ask pressure, and follow-through requirements
- Risk management rules covering stop loss, target definition, max account loss, and position caps
- Event filters for earnings, economic releases, and Federal Reserve announcements
- Logging and audit requirements for every trade

Detailed interpretation and implementation sequencing live in:

- [docs/design.md](C:\Users\Girish\Desktop\CodexTrading\docs\design.md)
- [docs/context.md](C:\Users\Girish\Desktop\CodexTrading\docs\context.md)
- [docs/project_tracker.md](C:\Users\Girish\Desktop\CodexTrading\docs\project_tracker.md)
- [docs/session_memory.md](C:\Users\Girish\Desktop\CodexTrading\docs\session_memory.md)
- [docs/trading_rules.md](C:\Users\Girish\Desktop\CodexTrading\docs\trading_rules.md)

## Project Layout

```text
CodexTrading/
|-- main.py
|-- pyproject.toml
|-- requirements.txt
|-- Dockerfile
|-- src/codextrading/
|   |-- __init__.py
|   |-- cli.py
|   |-- config.py
|   |-- ib_client.py
|   `-- service.py
|-- tests/
|-- docs/
`-- .github/
```

## Prerequisites

1. Python 3.11 or newer
2. Interactive Brokers TWS or IB Gateway running locally
3. API access enabled in TWS or Gateway

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py --symbols AAPL --host 127.0.0.1 --port 7497 --client-id 101 --duration 20
```

Example snapshot mode:

```bash
python main.py --symbols AAPL --snapshot
```

## Commands

Run tests:

```bash
pytest
```

Run lint checks:

```bash
ruff check .
```

Build distributable artifacts:

```bash
python -m build
```

Start a memory-tracked project session:

```bash
python main.py memory start --project CodexTrading --title "Session handoff" --objective "Capture current implementation state"
```

Build a semantic brief for the next session:

```bash
python main.py memory brief --project CodexTrading --query "What should I know before continuing this project?"
```

Automatically capture a tool run into session memory:

```bash
python main.py memory exec --project CodexTrading --session-id <id> -- python -m pytest
```

Developer wrapper for everyday commands:

```powershell
.\dev.ps1 test
.\dev.ps1 lint
.\dev.ps1 build
.\dev.ps1 close
```

## CI/CD

GitHub Actions are included for:

- Continuous integration on pushes and pull requests
- Artifact builds for wheels and source distributions
- Container image build and publish to GitHub Container Registry on release or manual dispatch

See:

- [.github/workflows/ci.yml](C:\Users\Girish\Desktop\CodexTrading\.github\workflows\ci.yml)
- [.github/workflows/cd.yml](C:\Users\Girish\Desktop\CodexTrading\.github\workflows\cd.yml)

## Roadmap

- Implement the full trading rules engine from `trading_rules.docx`
- Add market context adapters for breadth, sector, and volatility filters
- Add execution, risk, and portfolio services
- Persist audit-grade trade logs and decision traces
- Add paper trading and production deployment profiles
- Add automatic wrappers that capture shell, test, and build observations into session memory

## Notes

- [`Stratergy.py`](C:\Users\Girish\Desktop\CodexTrading\Stratergy.py) is preserved as a legacy prototype reference.
- The new codebase is structured for expansion and testing rather than embedding all behavior in one script.
