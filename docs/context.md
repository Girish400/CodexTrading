# Project Context

## Purpose

This repository is being shaped into a production-grade Interactive Brokers trading platform. The immediate deliverable is a stable market data entry point for AAPL using `ibapi` and `asyncio`, while the medium-term target is a rules-driven trading engine built from `trading_rules.docx`.

## Current Repository State

- `trading_rules.docx` is the source of truth for strategy, filtering, risk, and execution requirements.
- `Stratergy.py` is a legacy prototype that contains early logic for opening checks, ORB logic, and momentum scanning.
- `main.py` and `src/gstrading/` form the new maintainable baseline.

## Rules Context

The rules document includes 100 checklist items. The main clusters are:

- Opening-window spread and size checks
- ORB bullish and bearish qualification
- Momentum confirmation from recent ticks
- Market, breadth, sector, and volatility context
- Volume, ATR, VWAP, MACD, RSI, and tape speed filters
- Risk sizing, stop, target, cooldown, and max loss controls
- Catalyst and event-driven exclusions
- Execution constraints such as limit orders and trade logging

## Assumptions

- Interactive Brokers TWS or Gateway is available locally for development and production connectivity.
- The current milestone is market data ingestion, not live order placement.
- Deployment will initially use GitHub Actions artifacts and container images, with environment-specific release wiring added later.

## Near-Term Build Sequence

1. Stabilize market data ingestion and logging.
2. Translate the checklist into machine-readable rule groups.
3. Build market context providers and a composable rules engine.
4. Add execution simulation, then paper trading, then guarded live execution.
5. Add observability, audit storage, and operator workflows.
