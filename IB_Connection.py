# --- Python 3.14+ fix ---
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import logging
import os
import time
from datetime import datetime, timedelta

import pandas as pd
from ib_insync import IB, Index, Option

logging.getLogger().setLevel(logging.CRITICAL)

# -------------------- SETTINGS --------------------
HOST = "127.0.0.1"
PORT = 7496
CLIENT_ID = 11

MARKET_DATA_TYPE = 3
EXPIRY_WINDOW_DAYS = 8
DELTA_THRESHOLD = -0.03

QUALIFY_BATCH_SIZE = 400
BATCH_SIZE = 80

OUTPUT_DIR = None

OUT_QUOTES_XLSX = "spx_spxw_chain_quotes.xlsx"
OUT_CHAIN_META = "spx_spxw_chain_metadata.csv"
OUT_ERRORS = "spx_run_error_summary.csv"

# NEW
STRIKE_DELTA_TARGET = -0.02
STRIKE_BDAYS = 2
# -------------------------------------------------


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def out_path(filename):
    base = OUTPUT_DIR or os.getcwd()
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, filename)


# =========================
# HELPERS
# =========================

def parse_expiry_yyyymmdd(s):
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except Exception:
        return None

def add_business_days(start_date, n):
    d = start_date
    remaining = n
    while remaining > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            remaining -= 1
    return d

def choose_expiry_on_or_after(expirations, target_date):
    exp_data = [(e, parse_expiry_yyyymmdd(e)) for e in expirations]
    exp_data = [(e, d) for e, d in exp_data if d]

    target_str = target_date.strftime("%Y%m%d")
    for e, _ in exp_data:
        if e == target_str:
            return e

    exp_data.sort(key=lambda x: x[1])
    for e, d in exp_data:
        if d >= target_date:
            return e

    return None

def pick_chain(chains, trading_class):
    for c in chains:
        if getattr(c, "tradingClass", None) == trading_class:
            return c
    return None

def build_put_contracts(symbol, trading_class, expiries, strikes, exchange):
    contracts = []
    ex = exchange or "SMART"
    for expiry in expiries:
        for strike in strikes:
            contracts.append(
                Option(symbol, expiry, float(strike), "P", ex, tradingClass=trading_class)
            )
    return contracts


def qualify_and_req_tickers_batched(ib, contracts):
    out = []
    for i in range(0, len(contracts), QUALIFY_BATCH_SIZE):
        batch = contracts[i:i+QUALIFY_BATCH_SIZE]
        qualified = ib.qualifyContracts(*batch)
        qualified = [c for c in qualified if getattr(c, "conId", 0)]

        for j in range(0, len(qualified), BATCH_SIZE):
            sub = qualified[j:j+BATCH_SIZE]
            out.extend(ib.reqTickers(*sub))
            ib.sleep(0)

    return out


def tickers_to_df(tickers, name):
    rows = []
    for t in tickers:
        c = t.contract
        g = t.modelGreeks or t.lastGreeks

        rows.append({
            "chain": name,
            "expiry": c.lastTradeDateOrContractMonth,
            "strike": c.strike,
            "right": c.right,
            "delta": getattr(g, "delta", None) if g else None,
            "bid": t.bid,
            "ask": t.ask
        })

    return pd.DataFrame(rows)


# =========================
# ⭐ NEW FUNCTION
# =========================

def lowest_put_strike_delta_ge_target_for_xbd_expiry(
    ib,
    delta_target=-0.02,
    business_days_ahead=2
):
    """
    Fully self-contained:
    - finds spot
    - gets chains
    - finds expiry ~N business days ahead
    - returns LOWEST strike with delta >= target

    Returns:
      (strike, expiry, bid, ask) OR (None, None, None, None)
    """

    # get SPX
    spx = Index("SPX", "CBOE", "USD")
    ib.qualifyContracts(spx)

    # spot
    try:
        [t] = ib.reqTickers(spx)
        spot = t.marketPrice()
    except Exception:
        spot = None

    chains = ib.reqSecDefOptParams(spx.symbol, "", spx.secType, spx.conId)
    chain_spx = pick_chain(chains, "SPX")
    chain_spxw = pick_chain(chains, "SPXW")

    target_date = add_business_days(datetime.now().date(), business_days_ahead)

    for chain in [chain_spxw, chain_spx]:
        if not chain:
            continue

        expiry = choose_expiry_on_or_after(chain.expirations, target_date)
        if not expiry:
            continue

        strikes = sorted(chain.strikes)

        # optional narrowing
        if spot:
            strikes = [s for s in strikes if spot * 0.5 <= s <= spot * 1.02] or strikes

        contracts = build_put_contracts(
            "SPX",
            chain.tradingClass,
            [expiry],
            strikes,
            chain.exchange
        )

        tickers = qualify_and_req_tickers_batched(ib, contracts)
        df = tickers_to_df(tickers, chain.tradingClass)

        df = df[
            (df["right"] == "P") &
            (df["delta"].notna()) &
            (df["delta"] >= delta_target) &
            (df["delta"] <= 0)
        ]

        if df.empty:
            continue

        df = df.sort_values(["strike", "delta"], ascending=[True, False])
        best = df.iloc[0]

        strike_out = float(best["strike"])
        expiry_out = str(best["expiry"])  # already 'YYYYMMDD'
        bid_out = None if pd.isna(best.get("bid")) else float(best.get("bid"))
        ask_out = None if pd.isna(best.get("ask")) else float(best.get("ask"))

        return strike_out, expiry_out, bid_out, ask_out

    return None, None, None, None


# =========================
# MAIN
# =========================

def main():
    start = time.perf_counter()

    ib = IB()
    ib.connect(HOST, PORT, clientId=CLIENT_ID)

    ib.reqMarketDataType(MARKET_DATA_TYPE)

    # ✅ CALL NEW FUNCTION
    strike, row = lowest_put_strike_delta_ge_target_for_xbd_expiry(
        ib,
        delta_target=STRIKE_DELTA_TARGET,
        business_days_ahead=STRIKE_BDAYS
    )

    if strike:
        log(f"✅ 2DTE strike (delta >= {STRIKE_DELTA_TARGET}): {strike}")
        log(f"Details: {row}")
    else:
        log("⚠️ No strike found")

    # (rest of your existing chain export can stay here if needed)

    ib.disconnect()

    log(f"Runtime: {time.perf_counter()-start:.2f}s")


if __name__ == "__main__":
    main()