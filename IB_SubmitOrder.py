# --- Python 3.14+ event loop fix (safe to keep) ---
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import logging
import csv
import os
from datetime import datetime, timedelta
import IB_Connection
from ib_insync import IB, Index, Option

# -----------------------
# Logging Setup
# -----------------------
logging.basicConfig(
    filename="spx_main.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    filemode="w"   # ✅ overwrite log file each run
)
logging.info("=== Script started ===")

CSV_FILE = "spx_fills.csv"
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "order_id", "price", "quantity", "time"])


# ----------------------------
# Helpers
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


def pick_chain(chains, trading_class: str):
    for c in chains:
        if getattr(c, "tradingClass", None) == trading_class:
            return c
    return None

if __name__ == "__main__":

    ib = IB()
    ib.RequestTimeout = 10

    ib.connect("127.0.0.1", 7496, clientId=11)
    logging.info("Connected to IB")

    ib.reqMarketDataType(1)  # delayed-frozen is safe

    strike, expiry, bid, ask = lowest_put_strike_in_pct_band_for_xbd_expiry(
        ib,
        min_pct=-0.15,
        max_pct=-0.04,
        target_pct=-0.05,
        business_days_ahead=1
    )

    print("RESULT:", strike, expiry, bid, ask)

    logging.info(f"Result: {strike}, {expiry}, {bid}, {ask}")

    ib.disconnect()