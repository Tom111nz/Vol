"""
SPX + SPXW option chain + quotes/greeks via ib_insync (TWS live).

CHANGE REQUESTED (best-effort):
- ONLY request PUTS, and ONLY OUTPUT rows where delta >= -0.03.
- Output each expiry to a new tab in spx_spxw_chain_quotes.xlsx (XLSX instead of CSV).

Important practical note:
- Delta is not known until you request market data/greeks.
  So this script requests ALL PUT contracts in the selected expiry window,
  then FILTERS the resulting rows to keep only those with delta >= -0.03.

Includes “nicer to use” improvements:
1) Suppress noisy console logging by setting root logger to CRITICAL.
2) Capture all errors via ib.errorEvent, aggregate counts + samples into CSV.
   - Suppress console output for Error 200 (No security definition) to avoid slowdowns.
3) Add data-quality columns: has_bid_ask, has_greeks.
4) Sanity-check market data type after reqMarketDataType.
5) Python 3.14+ import fix: ensure a loop exists before importing ib_insync.
6) Batch qualifyContracts + reqTickers to avoid huge single requests.
7) Timer: print total script runtime.

Outputs:
- spx_spxw_chain_quotes.xlsx           (one worksheet per expiry)
- spx_spxw_chain_metadata.csv
- spx_run_error_summary.csv
"""

# --- Python 3.14+ fix: ensure there is an event loop before importing ib_insync ---
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
# -------------------------------------------------------------------------------

import logging
import os
import time
from datetime import datetime, timedelta

import pandas as pd
from ib_insync import IB, Index, Option


# -------------------- LOGGING / NOISE CONTROL --------------------
logging.getLogger().setLevel(logging.CRITICAL)
# ---------------------------------------------------------------


# -------------------- USER SETTINGS --------------------
HOST = "127.0.0.1"
PORT = 7496              # TWS LIVE commonly 7496; must match TWS "Socket port"
CLIENT_ID = 11

# Market data type:
# 1=live, 2=frozen, 3=delayed, 4=delayed-frozen
MARKET_DATA_TYPE = 3     # set to 1 for live if you have subscriptions

# Rolling window for expirations:
EXPIRY_WINDOW_DAYS = 8   # example: next 8 days

# Filter: only keep puts with delta >= this threshold:
DELTA_THRESHOLD = -0.03

# Batch sizes:
QUALIFY_BATCH_SIZE = 400   # contract qualification batches
BATCH_SIZE = 80            # reqTickers batches

# Output directory (None => current working directory).
OUTPUT_DIR = None

OUT_QUOTES_XLSX = "spx_spxw_chain_quotes.xlsx"
OUT_CHAIN_META = "spx_spxw_chain_metadata.csv"
OUT_ERRORS = "spx_run_error_summary.csv"
# -------------------------------------------------------


def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def out_path(filename: str) -> str:
    base = OUTPUT_DIR or os.getcwd()
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, filename)


def attach_error_logger(ib: IB):
    """
    Capture errors via errorEvent and write a summary to CSV.
    Suppress noisy console spam (notably Error 200) while still counting + sampling.
    """
    error_counts = {}
    error_samples = {}

    # Suppress these from console (still count + sample to CSV)
    SUPPRESS_CONSOLE_CODES = {200, 10090}

    def on_error(reqId, errorCode, errorString, contract):
        error_counts[errorCode] = error_counts.get(errorCode, 0) + 1

        # store only the first sample for each error code (avoid repeated str(contract) overhead)
        if errorCode not in error_samples:
            error_samples[errorCode] = {
                "reqId": reqId,
                "errorString": errorString,
                "contract": str(contract) if contract else ""
            }

        # suppress noisy codes from console
        if errorCode in SUPPRESS_CONSOLE_CODES:
            return

        # print others (actionable)
        if contract:
            log(f"Error {errorCode}, reqId {reqId}: {errorString}, contract: {contract}")
        else:
            log(f"Error {errorCode}, reqId {reqId}: {errorString}")

    ib.errorEvent += on_error
    return error_counts, error_samples


def sanity_check_market_data_type(ib: IB, spx: Index):
    """
    Best-effort sanity check: request a snapshot and read ticker.marketDataType.
    """
    try:
        t = ib.reqMktData(spx, snapshot=True)
        ib.sleep(1.0)
        return getattr(t, "marketDataType", None)
    except Exception:
        return None


def pick_chain(chains, trading_class: str):
    """Pick chain by tradingClass ('SPX' or 'SPXW'), preferring SMART exchange if present."""
    candidates = [c for c in chains if getattr(c, "tradingClass", None) == trading_class]
    if not candidates:
        return None
    for c in candidates:
        if getattr(c, "exchange", None) == "SMART":
            return c
    return candidates[0]


def parse_expiry_yyyymmdd(s: str):
    """Parse IB expiry string 'YYYYMMDD' into date. Return None if parsing fails."""
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except Exception:
        return None


def expiries_in_window(expiry_list):
    """
    Filter expirations to those within [today, today+EXPIRY_WINDOW_DAYS].
    expiry_list elements are 'YYYYMMDD' strings as returned by IB.
    """
    today = datetime.now().date()
    end = today + timedelta(days=EXPIRY_WINDOW_DAYS)

    keep = []
    for e in expiry_list:
        d = parse_expiry_yyyymmdd(e)
        if d is None:
            continue
        if today <= d <= end:
            keep.append(e)

    return sorted(keep)


def build_put_contracts(symbol: str, trading_class: str, expiries, strikes, exchange: str):
    """
    Build PUT Option contracts for all expiries and ALL strikes.
    Uses the chain's exchange if provided.
    """
    contracts = []
    ex = exchange or "SMART"
    for expiry in expiries:
        for strike in strikes:
            k = float(strike)
            contracts.append(Option(symbol, expiry, k, "P", ex, tradingClass=trading_class))
    return contracts


def qualify_and_req_tickers_batched(ib: IB, contracts):
    """
    Qualify contracts in batches and request tickers for qualified contracts only.
    """
    tickers_out = []

    for i in range(0, len(contracts), QUALIFY_BATCH_SIZE):
        q_batch = contracts[i:i + QUALIFY_BATCH_SIZE]
        qualified = ib.qualifyContracts(*q_batch)

        # Keep only successful qualifications (have conId)
        qualified = [c for c in qualified if getattr(c, "conId", 0)]
        if not qualified:
            ib.sleep(0)
            continue

        for j in range(0, len(qualified), BATCH_SIZE):
            md_batch = qualified[j:j + BATCH_SIZE]
            tickers_out.extend(ib.reqTickers(*md_batch))
            ib.sleep(0)

    return tickers_out


def tickers_to_df(tickers, chain_name: str):
    rows = []
    for t in tickers:
        c = t.contract
        g = t.modelGreeks or t.lastGreeks

        rows.append({
            "chain": chain_name,
            "conId": getattr(c, "conId", None),
            "localSymbol": getattr(c, "localSymbol", None),
            "expiry": getattr(c, "lastTradeDateOrContractMonth", None),
            "strike": getattr(c, "strike", None),
            "right": getattr(c, "right", None),
            "exchange": getattr(c, "exchange", None),
            "tradingClass": getattr(c, "tradingClass", None),

            "bid": getattr(t, "bid", None),
            "ask": getattr(t, "ask", None),
            "last": getattr(t, "last", None),
            "close": getattr(t, "close", None),

            "iv": getattr(g, "impliedVol", None) if g else None,
            "delta": getattr(g, "delta", None) if g else None,
            "gamma": getattr(g, "gamma", None) if g else None,
            "vega": getattr(g, "vega", None) if g else None,
            "theta": getattr(g, "theta", None) if g else None,
        })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["has_bid_ask"] = df["bid"].notna() & df["ask"].notna()
        df["has_greeks"] = df["delta"].notna()
    else:
        df["has_bid_ask"] = pd.Series(dtype=bool)
        df["has_greeks"] = pd.Series(dtype=bool)

    return df


def chain_meta_to_rows(chain, chain_name: str):
    expiries = sorted(getattr(chain, "expirations", []) or [])
    strikes = sorted(getattr(chain, "strikes", []) or [])
    return [{
        "chain": chain_name,
        "exchange": getattr(chain, "exchange", None),
        "underlyingConId": getattr(chain, "underlyingConId", None),
        "tradingClass": getattr(chain, "tradingClass", None),
        "multiplier": getattr(chain, "multiplier", None),
        "numExpirations": len(expiries),
        "numStrikes": len(strikes),
        "firstExpiry": expiries[0] if expiries else None,
        "lastExpiry": expiries[-1] if expiries else None,
        "minStrike": strikes[0] if strikes else None,
        "maxStrike": strikes[-1] if strikes else None,
    }]


def filter_puts_by_delta(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """
    Keep only rows that are PUTs with delta >= threshold.
    Rows with missing delta are dropped.
    """
    if df.empty:
        return df

    return df[
        (df["right"] == "P") &
        (df["delta"].notna()) &
        (df["delta"] >= threshold)
    ].copy()


def safe_sheet_name(name: str) -> str:
    """
    Excel sheet name rules:
    - max 31 chars
    - cannot contain: : \ / ? * [ ]
    Expiry strings are safe; still sanitize defensively.
    """
    bad = [":", "\\", "/", "?", "*", "[", "]"]
    for ch in bad:
        name = name.replace(ch, "_")
    return name[:31] if len(name) > 31 else name


def write_expiry_tabs_xlsx(df: pd.DataFrame, xlsx_path: str):
    """
    Write one worksheet per expiry into a single XLSX workbook.
    Each sheet includes BOTH SPX and SPXW rows for that expiry.
    """
    # If df is empty, still create a workbook with a single 'EMPTY' tab.
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        if df.empty:
            pd.DataFrame([{"info": "No rows after filtering"}]).to_excel(writer, sheet_name="EMPTY", index=False)
            return

        # Ensure deterministic ordering
        df = df.sort_values(["expiry", "chain", "strike", "right"], kind="mergesort")

        for expiry, sub in df.groupby("expiry", sort=True):
            sheet = safe_sheet_name(str(expiry))
            sub.to_excel(writer, sheet_name=sheet, index=False)

        # Optional: add a Summary tab
        summary = (
            df.groupby(["expiry", "chain"], dropna=False)
              .size()
              .reset_index(name="rows")
              .sort_values(["expiry", "chain"])
        )
        summary.to_excel(writer, sheet_name="SUMMARY", index=False)


def main():
    start_time = time.perf_counter()

    log(f"Working directory: {os.getcwd()}")
    if OUTPUT_DIR:
        log(f"Output directory: {OUTPUT_DIR}")

    ib = IB()
    error_counts, error_samples = attach_error_logger(ib)

    log(f"Connecting to TWS {HOST}:{PORT} clientId={CLIENT_ID} ...")
    ib.connect(HOST, PORT, clientId=CLIENT_ID)
    log("Connected.")

    ib.reqMarketDataType(MARKET_DATA_TYPE)
    log(f"Requested market data type: {MARKET_DATA_TYPE} (1=live,2=frozen,3=delayed,4=delayed-frozen)")

    spx = Index("SPX", "CBOE", "USD")
    ib.qualifyContracts(spx)

    mdt = sanity_check_market_data_type(ib, spx)
    log(f"Sanity check: ticker.marketDataType reported as {mdt}" if mdt is not None
        else "Sanity check: could not read ticker.marketDataType")

    # Spot is optional (useful context only)
    try:
        [ticker] = ib.reqTickers(spx)
        spot = ticker.marketPrice()
    except Exception:
        spot = None
    log(f"SPX spot: {spot if spot is not None else 'N/A'}")

    log("Requesting option chain definitions (reqSecDefOptParams) ...")
    chains = ib.reqSecDefOptParams(spx.symbol, "", spx.secType, spx.conId)

    chain_spx = pick_chain(chains, "SPX")
    chain_spxw = pick_chain(chains, "SPXW")

    meta_rows = []
    if chain_spx:
        meta_rows += chain_meta_to_rows(chain_spx, "SPX")
    if chain_spxw:
        meta_rows += chain_meta_to_rows(chain_spxw, "SPXW")

    if meta_rows:
        meta_file = out_path(OUT_CHAIN_META)
        pd.DataFrame(meta_rows).to_csv(meta_file, index=False)
        log(f"Saved chain metadata: {meta_file}")
    else:
        log("No SPX/SPXW chains found. Exiting.")
        ib.disconnect()
        return

    frames = []

    # --- SPX monthlies: ALL strikes, expirations within window, PUTS ONLY ---
    if chain_spx:
        expiries = expiries_in_window(getattr(chain_spx, "expirations", []) or [])
        strikes = sorted(getattr(chain_spx, "strikes", []) or [])

        log(f"SPX: expiries in next {EXPIRY_WINDOW_DAYS} days = {len(expiries)} | strikes = {len(strikes)}")

        if expiries and strikes:
            contracts = build_put_contracts(
                symbol="SPX",
                trading_class=chain_spx.tradingClass,
                expiries=expiries,
                strikes=strikes,
                exchange=getattr(chain_spx, "exchange", None),
            )
            log(f"SPX PUT contracts to qualify/request: {len(contracts)}")
            tickers = qualify_and_req_tickers_batched(ib, contracts)
            frames.append(tickers_to_df(tickers, "SPX"))
        else:
            log("SPX: no expiries or strikes found in the window.")

    # --- SPXW weeklies/dailies: ALL strikes, expirations within window, PUTS ONLY ---
    if chain_spxw:
        expiries = expiries_in_window(getattr(chain_spxw, "expirations", []) or [])
        strikes = sorted(getattr(chain_spxw, "strikes", []) or [])

        log(f"SPXW: expiries in next {EXPIRY_WINDOW_DAYS} days = {len(expiries)} | strikes = {len(strikes)}")

        if expiries and strikes:
            contracts = build_put_contracts(
                symbol="SPX",
                trading_class=chain_spxw.tradingClass,
                expiries=expiries,
                strikes=strikes,
                exchange=getattr(chain_spxw, "exchange", None),
            )
            log(f"SPXW PUT contracts to qualify/request: {len(contracts)}")
            tickers = qualify_and_req_tickers_batched(ib, contracts)
            frames.append(tickers_to_df(tickers, "SPXW"))
        else:
            log("SPXW: no expiries or strikes found in the window.")

    # Save outputs (filtered) to XLSX with one tab per expiry
    if frames:
        df_all = pd.concat(frames, ignore_index=True)
        total_rows = len(df_all)

        df = filter_puts_by_delta(df_all, DELTA_THRESHOLD)
        kept_rows = len(df)

        xlsx_file = out_path(OUT_QUOTES_XLSX)
        write_expiry_tabs_xlsx(df, xlsx_file)

        has_quotes = int(df["has_bid_ask"].sum()) if "has_bid_ask" in df.columns and not df.empty else 0
        has_greeks = int(df["has_greeks"].sum()) if "has_greeks" in df.columns and not df.empty else 0

        log(f"Saved quotes workbook: {xlsx_file}")
        log(f"Rows received (all puts): {total_rows} | Rows kept (delta >= {DELTA_THRESHOLD}): {kept_rows}")
        log(f"Kept rows with bid/ask: {has_quotes} | kept rows with greeks: {has_greeks}")

        log("Preview (kept rows):")
        print(df.head(20))
    else:
        log("No quote frames collected.")

    # Error summary CSV
    summary_rows = []
    for code, count in sorted(error_counts.items(), key=lambda x: x[0]):
        sample = error_samples.get(code, {})
        summary_rows.append({
            "errorCode": code,
            "count": count,
            "sampleReqId": sample.get("reqId", ""),
            "sampleErrorString": sample.get("errorString", ""),
            "sampleContract": sample.get("contract", ""),
        })

    err_file = out_path(OUT_ERRORS)
    pd.DataFrame(summary_rows).to_csv(err_file, index=False)
    log(f"Saved error summary: {err_file}")

    if summary_rows:
        top = ", ".join([f"{r['errorCode']}={r['count']}" for r in summary_rows[:10]])
        log(f"Error counts (first 10 codes): {top}")

    ib.disconnect()
    log("Disconnected.")

    elapsed = time.perf_counter() - start_time
    log(f"Total runtime: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")


if __name__ == "__main__":
    main()