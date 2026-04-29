# Trading Rules

This Markdown document is a structured conversion of [trading_rules.docx](C:\Users\Girish\Desktop\GSTrading\trading_rules.docx). The original 100 checklist items are preserved, but reorganized into practical operating categories so they are easier to review, implement, and test.

## Categorization Model

- `Window and Trigger Timing`: when a setup is allowed to activate
- `Opening Imbalance`: opening spread and size-based setup filters
- `ORB Setup`: one-minute opening range breakout requirements
- `Momentum Setup`: fast-tape momentum qualification
- `Market Context`: index, breadth, sector, and volatility alignment
- `Liquidity and Participation`: volume, ATR, spread, and tape quality
- `Technical Alignment`: trend, VWAP, MACD, RSI, and candle structure checks
- `Entry Confirmation and Location`: confirmation tick and price-location rules
- `Catalyst and Event Filters`: news, earnings, macro, and halt exclusions
- `Risk and Trade Management`: sizing, stops, targets, position caps, cooldowns, and journaling

## 1. Window and Trigger Timing

- `Rule 1`: Execute only between `06:30:00-06:30:59 PST`
- `Rule 6`: ORB executes only between `06:31:00-06:31:02 PST`
- `Rule 72`: Avoid all trades between `11:00 AM-1:00 PM EST`
- `Rule 73`: If trading in the dead zone, increase volume thresholds
- `Rule 74`: If trading in the dead zone, increase price-movement thresholds

## 2. Opening Imbalance

- `Rule 2`: Bid-ask spread must be `<= $0.03`
- `Rule 3`: Ask size `>= 50,000` is a bullish signal
- `Rule 4`: Bid size `>= 50,000` is a bearish signal
- `Rule 5`: Stock must not already be triggered

## 3. ORB Setup

### Bullish ORB

- `Rule 7`: Pre-market volume `> 1,000`
- `Rule 8`: Post-open volume increase `> 800`
- `Rule 9`: Shortable shares `> 100,000`
- `Rule 10`: Spread `< $0.03`
- `Rule 11`: Trade rate `> 1,000`
- `Rule 12`: Trade count `> 1,000`
- `Rule 13`: Volume rate `> 50,000`
- `Rule 14`: Last price `> VWAP`
- `Rule 15`: Last price `> Open`
- `Rule 16`: Last price `> Previous Close`
- `Rule 17`: `(High - Last) < 0.11`
- `Rule 18`: `(Last - Open) > 0.24`
- `Rule 19`: `Low < VWAP`

### Bearish ORB

- `Rule 20`: Last `< VWAP`
- `Rule 21`: Last `< Open`
- `Rule 22`: Last `< Previous Close`
- `Rule 23`: `(Last - Low) < 0.11`
- `Rule 24`: `(Open - Last) > 0.24`
- `Rule 25`: `High > VWAP`

## 4. Momentum Setup

- `Rule 26`: Spread `<= $0.03`
- `Rule 27`: Track the last `600` ticks
- `Rule 28`: Price move `>= $0.30` within tracked ticks
- `Rule 29`: Minimum `4` ticks required
- `Rule 30`: Volume increase `>= 50,000` within tracked ticks
- `Rule 31`: `100%` up ticks required for bullish confirmation
- `Rule 32`: `100%` down ticks required for bearish confirmation

## 5. Market Context

- `Rule 33`: Long trades only if the market index is above VWAP
- `Rule 34`: Short trades only if the market index is below VWAP
- `Rule 35`: Long trades only if advancers outnumber decliners
- `Rule 36`: Short trades only if decliners outnumber advancers
- `Rule 37`: Trade only if the sector trend matches the trade direction
- `Rule 38`: Avoid isolated single-stock moves without sector confirmation
- `Rule 97`: At least `2` market-context filters from Section 2 must pass before entry
- `Rule 98`: If VIX is above `35`, do not trade without materially increasing thresholds

## 6. Liquidity and Participation

- `Rule 39`: RVOL must be `>= 2.0x` versus the 10-day same-time average
- `Rule 40`: Dollar volume must be `>= $5,000,000`
- `Rule 41`: Volume must be increasing over short intervals
- `Rule 42`: Tape speed must be accelerating
- `Rule 43`: Trade rate must be actively increasing
- `Rule 44`: Trade rate `> 1,000` at signal time
- `Rule 45`: Trade count `> 1,000` at signal time
- `Rule 46`: `ATR(14) >= 0.50`
- `Rule 47`: Price move must be `>= 0.3 x ATR`
- `Rule 55`: Bid/ask ratio must be at least `2:1`
- `Rule 56`: Bid/ask ratio `>= 3:1` preferred
- `Rule 57`: Average spread across last `10` ticks must be `<= $0.03`
- `Rule 58`: High volume plus tight range suggests hidden accumulation
- `Rule 59`: Look for repeated bid or ask absorption before entry
- `Rule 76`: Do not trade stocks priced below `$2.00`
- `Rule 77`: Do not trade stocks with average daily volume below `500,000`
- `Rule 89`: Prefer stocks with float under `50 million` shares for momentum setups

## 7. Technical Alignment

- `Rule 48`: Long entries only when the 5-minute chart is in an uptrend
- `Rule 49`: Short entries only when the 5-minute chart is in a downtrend
- `Rule 50`: Long entries only when price is above VWAP
- `Rule 51`: Short entries only when price is below VWAP
- `Rule 52`: Price must be at least `$0.15` away from VWAP before entry
- `Rule 53`: MACD must align with the trade direction
- `Rule 54`: Do not enter on MACD divergence
- `Rule 60`: Reject candles where the wick is larger than the body
- `Rule 61`: Accept only strong body candle structure
- `Rule 90`: RSI must not be above `80` for long entries
- `Rule 91`: RSI must not be below `20` for short entries

## 8. Entry Confirmation and Location

- `Rule 62`: Wait for the next tick after a signal fires before entering
- `Rule 63`: Enter only if the next tick continues in the signal direction
- `Rule 64`: Avoid trading near Previous Day High
- `Rule 65`: Avoid trading near Previous Day Low
- `Rule 66`: Avoid trading near round whole-number price levels
- `Rule 67`: Do not take longs directly into known resistance
- `Rule 68`: Do not take shorts directly into known support
- `Rule 84`: If a stock gaps up more than `10%`, wait for a confirmed pullback and base
- `Rule 94`: Pre-market high must hold as support before a long entry
- `Rule 95`: Short entries must occur below confirmed pre-market low
- `Rule 96`: Entry price must not be more than `3%` away from the original trigger price

## 9. Catalyst and Event Filters

- `Rule 69`: A news catalyst must be present
- `Rule 70`: Avoid stocks with a gap greater than `5%`
- `Rule 71`: If gap is greater than `4%`, require exceptional above-average volume
- `Rule 82`: Do not trade during Federal Reserve rate announcements
- `Rule 83`: Do not trade during high-impact economic releases such as CPI, NFP, or FOMC
- `Rule 92`: Do not trade halted stocks or stocks in pending-news state
- `Rule 93`: Avoid stocks with earnings due in the next `24` hours unless earnings is the catalyst

## 10. Risk and Trade Management

- `Rule 75`: Enforce a minimum `5`-minute cooldown between trades on the same stock
- `Rule 78`: Risk no more than `1%` of total account value per trade
- `Rule 79`: Stop loss must be defined before entry
- `Rule 80`: Profit target must be defined before entry
- `Rule 81`: Risk/reward ratio must be at least `2:1`
- `Rule 85`: Never average into a losing position
- `Rule 86`: Maximum of `3` open positions at one time
- `Rule 87`: If daily account loss exceeds `2%`, stop trading for the rest of the session
- `Rule 88`: Do not re-enter a stock stopped out earlier in the same session
- `Rule 99`: All entries must be limit orders
- `Rule 100`: Every trade must be logged with entry, exit, triggered rules, and outcome

## Implementation Priority

If these rules are implemented as software, the practical build order should be:

1. `Window and Trigger Timing`
2. `Opening Imbalance`, `ORB Setup`, and `Momentum Setup`
3. `Liquidity and Participation`
4. `Market Context`
5. `Technical Alignment`
6. `Entry Confirmation and Location`
7. `Catalyst and Event Filters`
8. `Risk and Trade Management`

## Notes for Engineering

- Several rules depend on data not currently provided by the basic `ibapi` market-data stream alone, including breadth, sector confirmation, VIX, ATR, RSI, MACD, economic calendar events, and earnings schedules.
- Rules `33-38`, `82-83`, `90-98`, and `100` imply additional services for market context, event data, and trade journaling.
- This document should be treated as the readable reference, while `trading_rules.docx` remains the original source artifact.
