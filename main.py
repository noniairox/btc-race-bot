"""Dual-horizon momentum bot for btc-race-24h-20261118-1444.

Long-only cbBTC/USDC bot speaking agent-fun/bars-replay/v1 via the
vendored shim. One position at most, full size (100% of cash) on entry.

Strategy, per batch (one 1-minute bar):
- Keep the history of closes.
- FLAT and return over 60 bars > +50 bps AND return over 90 bars
  > +30 bps -> buy with all cash.
- HOLDING and return over 60 bars < -40 bps, OR the close has fallen
  1.0% from the peak close since entry (trailing stop) -> sell all.
- No orders while warming up. No clock, no environment, no random:
  every decision comes only from the closes in the hello/batch stream,
  so two runs produce identical action logs.

Orders fill at the next bar's open (latency 1 bar), so the decision
bar's close is the signal and the next open is the fill.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
MAX_SLIPPAGE_BPS = 200

# Return thresholds, in basis points.
ENTRY_R60_BPS = 50
ENTRY_R90_BPS = 30
EXIT_R60_BPS = -40
TRAILING_STOP_BPS = 100  # 1.0% below the peak close since entry.

_closes = []        # close (int, price_scale 5) of every bar seen, in order
_peak_since_entry = 0  # highest close seen while holding, 0 when flat


def _return_bps(now, then):
    """Return from `then` to `now` in basis points (float, deterministic)."""
    return (now / then - 1.0) * 10000.0


def on_batch(state, batch):
    global _peak_since_entry
    close = state.close(SYMBOL)
    if close is None:
        return []
    _closes.append(close)

    if state.warming_up:
        return []

    holding = state.positions.get(SYMBOL)
    qty = holding.qty if holding is not None else 0

    if qty > 0:
        # Holding: track the peak close since entry for the trailing stop.
        if close > _peak_since_entry:
            _peak_since_entry = close
        r60 = None
        if len(_closes) >= 61:
            r60 = _return_bps(_closes[-1], _closes[-61])
        fell_from_peak = (
            _peak_since_entry > 0
            and close * 10000 < _peak_since_entry * (10000 - TRAILING_STOP_BPS)
        )
        # Exact integer check: close more than 1.0% below the peak close
        # since entry (close / peak < 0.99), no float rounding involved.
        if (r60 is not None and r60 < EXIT_R60_BPS) or fell_from_peak:
            _peak_since_entry = 0
            return [
                {
                    "side": "sell",
                    "symbol": SYMBOL,
                    "qty": qty,
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }
            ]
        return []

    # Flat: wait for enough history, then check both momentum horizons.
    _peak_since_entry = 0
    if len(_closes) < 91:
        return []
    r60 = _return_bps(_closes[-1], _closes[-61])
    r90 = _return_bps(_closes[-1], _closes[-91])
    if r60 > ENTRY_R60_BPS and r90 > ENTRY_R90_BPS:
        cash = int(state.cash)
        if cash < 1000000:  # below the 1 USDC min notional, do nothing
            return []
        _peak_since_entry = close
        return [
            {
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": cash,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }
        ]
    return []


if __name__ == "__main__":
    # Guarded so the module can be imported (e.g. by a local replay
    # harness that calls on_batch directly) without starting the wire loop.
    makefun_bars.run(on_batch)
