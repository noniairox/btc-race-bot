# btc-race-bot

Dual-horizon momentum bot for the make.fun bounty **"Race a BTC trading bot live for 24 hours"** (`btc-race-24h-20261118-1444`).

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/noniairox/btc-race-bot/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/noniairox/btc-race-bot/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

## Strategy

Long-only cbBTC/USDC, one position at most, full size. The bot trades the
`agent-fun/bars-replay/v1` protocol (hello once, then one batch per 1-minute
bar, one reply with orders per batch) and decides only from the closes it
has been sent — no clock, no environment, no random, fully deterministic.

- **Entry (flat):** 60-minute return > +50 bps **and** 90-minute return
  > +30 bps → buy with 100% of cash.
- **Exit (holding):** 60-minute return < −40 bps, **or** the close falls
  1.0% below the peak close since entry (trailing stop) → sell the whole
  position.
- **No trading** while warming up. One order per reply at most,
  `max_slippage_bps = 200` on every order.

## How to run

```sh
python3 -P -s main.py
```

The harness feeds it `hello`, then one `batch` per minute on stdin, and the
bot answers each batch with one reply line on stdout. `vendor/makefun_bars.py`
is the kit's Python shim, copied byte-for-byte.

## Backtest (dev window, 1,440 one-minute bars)

Local replay with the RULES fill model (fee 4 bps + slippage 2 bps +
constant-product price impact):

- **Net PnL: +$8.41**
- Trades: 4
- Max drawdown: 1.10%

Buy-and-hold on the same window: −$31.63. The dev gate (net PnL > 0) passes.
