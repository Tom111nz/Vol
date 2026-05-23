# --- Python 3.14+ event loop fix (safe to keep) ---
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from datetime import datetime, timedelta
from ib_insync import IB, Index, Option
import logging

# ----------------------------
# Small helpers (used by function)
# ----------------------------

def parse_expiry_yyyymmdd(s: str):
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except Exception:
        return None


def add_business_days(start_date, n: int):
    d = start_date
    remaining = n
    while remaining > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:  # Mon-Fri
            remaining -= 1
    return d


def choose_expiry_on_or_after(expirations, target_date):
    """Pick the first expiry on/after target_date from a list of YYYYMMDD strings."""
    exp_data = [(e, parse_expiry_yyyymmdd(e)) for e in expirations]
    exp_data = [(e, d) for e, d in exp_data if d]

    # Exact match preferred
    target_str = target_date.strftime("%Y%m%d")
    for e, _ in exp_data:
        if e == target_str:
            return e

    # Otherwise earliest >= target_date
    exp_data.sort(key=lambda x: x[1])
    for e, d in exp_data:
        if d >= target_date:
            return e

    return None


def pick_chain(chains, trading_class: str):
    """Find the option chain with the given tradingClass."""
    for c in chains:
        if getattr(c, "tradingClass", None) == trading_class:
            return c
    return None


def build_put_contracts(symbol, trading_class, expiry, strikes):
    """Build PUT Option contracts for a single expiry."""
    ex = "SMART"  # SMART is generally most stable for IB option lookup
    return [
        Option(symbol, expiry, float(strike), "P", ex, tradingClass=trading_class)
        for strike in strikes
    ]


def qualify_and_req_tickers_batched(ib: IB, contracts, qualify_batch_size=200, ticker_batch_size=50):
    """
    Qualify then request tickers in batches to avoid pacing/size issues.
    Returns a flat list of tickers.
    """
    out = []
    for i in range(0, len(contracts), qualify_batch_size):
        batch = contracts[i:i + qualify_batch_size]

        try:
            qualified = ib.qualifyContracts(*batch)
        except TimeoutError:
            continue

        qualified_ok = [c for c in qualified if getattr(c, "conId", 0)]
        for j in range(0, len(qualified_ok), ticker_batch_size):
            sub = qualified_ok[j:j + ticker_batch_size]
            out.extend(ib.reqTickers(*sub))
            ib.sleep(0)  # yield to keep message processing healthy
    return out

def lowest_put_strike_in_pct_band_for_xbd_expiry(
    ib: IB,
    min_pct: float = -0.15,   # band lower bound (-15%)
    max_pct: float = -0.04,   # band upper bound (-5%)
    target_pct: float = -0.05,  # ✅ NEW constraint (must be <= this)
    business_days_ahead: int = 1,
):
    """
    Selects a PUT option whose strike lies between [min_pct, max_pct]
    relative to spot AND whose moneyness <= max_moneyness.

    Moneyness := strike / spot - 1

    Returns:
        (strike, expiry_yyyymmdd, bid, ask)
        or (None, None, None, None)
    """

    # --- Underlying ---
    spx = Index("SPX", "CBOE", "USD")
    ib.qualifyContracts(spx)

    if not getattr(spx, "conId", None):
        logging.error("SPX contract qualification failed")
        return None, None, None, None

    # --- Get spot ---
    try:
        [ticker] = ib.reqTickers(spx)
        spot = ticker.marketPrice()
    except Exception as e:
        logging.exception(f"Failed to get SPX price: {e}")
        return None, None, None, None

    if spot is None:
        logging.error("SPX price unavailable")
        return None, None, None, None

    logging.info(f"SPX spot: {spot}")

    # --- Target band ---
    target_low = spot * (1 + min_pct)
    target_high = spot * (1 + max_pct)

    logging.info(f"Band: {target_low:.2f} → {target_high:.2f}")
    logging.info(f"Max moneyness constraint: {target_pct:.4f}")

    # --- Get chains ---
    chains = ib.reqSecDefOptParams(spx.symbol, "", spx.secType, spx.conId)

    chain_spx = pick_chain(chains, "SPX")
    chain_spxw = pick_chain(chains, "SPXW")

    target_date = add_business_days(datetime.now().date(), business_days_ahead)

    # Prefer SPXW first
    for chain in (chain_spxw, chain_spx):
        if not chain:
            continue

        expiry = choose_expiry_on_or_after(chain.expirations, target_date)
        if not expiry:
            continue

        logging.info(f"Using {chain.tradingClass} expiry {expiry}")

        # ✅ Use only valid contracts
        template = Option(
            symbol="SPX",
            lastTradeDateOrContractMonth=expiry,
            strike=0,
            right="P",
            exchange=chain.exchange,
            tradingClass=chain.tradingClass
        )

        try:
            details = ib.reqContractDetails(template)
        except Exception as e:
            logging.exception(f"ContractDetails failed: {e}")
            continue

        contracts = [d.contract for d in details if d.contract.right == "P"]

        if not contracts:
            continue

        # --- Filter ---
        filtered = []
        for c in contracts:
            strike = float(c.strike)

            # % band filter
            if not (target_low <= strike <= target_high):
                continue

            # ✅ moneyness constraint
            moneyness = strike / spot - 1
            if moneyness > target_pct:
                continue

            filtered.append(c)

        if not filtered:
            logging.info("No contracts after filtering")
            continue

        logging.info(f"Filtered count: {len(filtered)}")

        # --- Get tickers ---
        tickers = ib.reqTickers(*filtered)

        # --- Selection (midpoint of band) ---
        target_mid = spot * (1 + target_pct)

        best = None
        best_diff = None

        for t in tickers:
            if not t.contract:
                continue

            strike = float(t.contract.strike)
            diff = abs(strike - target_mid)

            if best is None or diff < best_diff:
                best = t
                best_diff = diff

        if best is None:
            continue

        c = best.contract

        return (
            float(c.strike),
            str(c.lastTradeDateOrContractMonth),
            None if best.bid is None else float(best.bid),
            None if best.ask is None else float(best.ask),
        )

    return None, None, None, None


# ----------------------------
# Optional usage example
# ----------------------------
if __name__ == "__main__":
    ib = IB()
    ib.RequestTimeout = 10
    ib.connect("127.0.0.1", 7496, clientId=11)
    ib.reqMarketDataType(4)

    strike, expiry, bid, ask = lowest_put_strike_delta_ge_target_for_xbd_expiry(
        ib,
        delta_target=-0.02,
        business_days_ahead=2
    )

    print("RESULT:", strike, expiry, bid, ask)
    ib.disconnect()