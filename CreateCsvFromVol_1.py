import os
import csv
import zipfile
from pathlib import Path

import pymysql as mdb
from LoadCBOEoptionsNew import insertVolData

# ---------- CONFIG ----------
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "Bright1"),
    "database": "vol_1",
    "port": int(os.environ.get("DB_PORT", 3306)),
    "charset": "utf8mb4",
}

OUTPUT_DIR = Path(r"C:\Temp\CBOE_History")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATE_START = "2004-12-31"
DATE_END = "2005-12-31"
FETCH_BATCH_SIZE = 5000
DELETE_CSV_AFTER_PROCESS = True

# ---------- CSV HEADER ----------
CSV_HEADERS = [
    "underlying_symbol", "quote_date", "root", "expiration", "strike", "option_type",
    "open", "high", "low", "close", "trade_volume",
    "bid_size_1545", "bid_1545", "ask_size_1545", "ask_1545",
    "underlying_bid_1545", "underlying_ask_1545",
    "implied_underlying_price_1545", "active_underlying_price_1545",
    "implied_volatility_1545", "delta_1545", "gamma_1545", "theta_1545",
    "vega_1545", "rho_1545",
    "bid_size_eod", "bid_eod", "ask_size_eod", "ask_eod",
    "underlying_bid_eod", "underlying_ask_eod",
    "vwap", "open_interest", "delivery_code"
]


# ---------- SQL ----------
SQL_DATES = """
SELECT DISTINCT LEFT(quote_date, 10) AS quote_date
FROM optionexpiry
WHERE quote_date >= %s AND < %s
ORDER BY quote_date;
"""
SQL_MAIN_PER_DATE = """
SELECT
    TRIM(oe.root),
    LEFT(oe.quote_date, 10),
    TRIM(oe.rootoriginal),
    LEFT(oe.expiration, 10),
    st.strike,
    TRIM(st.option_type),
    EoD.opn, EoD.high, EoD.low, EoD.clos, EoD.trade_volume,
    og.bid_size_1545, og.bid_1545, og.ask_size_1545, og.ask_1545,
    und.underlying_bid_1545, und.underlying_ask_1545,
    und.implied_underlying_price_1545, und.active_underlying_price_1545,
    og.implied_volatility_1545, og.delta_1545, og.gamma_1545,
    og.theta_1545, og.vega_1545, og.rho_1545,
    EoD.bid_size_eod, EoD.bid_eod, EoD.ask_size_eod, EoD.ask_eod,
    und.underlying_bid_eod, und.underlying_ask_eod,
    EoD.vwap, EoD.open_interest, EoD.delivery_code
FROM optionexpiry oe
LEFT JOIN optiongreeks og ON og.optionexpiryID = oe.ID
LEFT JOIN Underlying und ON und.optionexpiryID = oe.ID
LEFT JOIN strike st ON st.ID = og.strikeid
LEFT JOIN EoD ON EoD.OptionExpiryID = oe.ID AND EoD.strikeID = st.ID
WHERE LEFT(oe.quote_date, 10) = %s
ORDER BY expiration, strike, option_type;
"""


# ---------- HELPERS ----------
def zip_file(csv_path: Path) -> Path:
    zip_path = csv_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_path, arcname=csv_path.name)
    return zip_path


def export_one_date(cursor, quote_date: str) -> Path:
    csv_path = OUTPUT_DIR / f"UnderlyingOptionsEODCalcs_{quote_date}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADERS)

        cursor.execute(SQL_MAIN_PER_DATE, (quote_date,))
        while True:
            batch = cursor.fetchmany(FETCH_BATCH_SIZE)
            if not batch:
                break
            writer.writerows(batch)

    return csv_path


# ---------- MAIN ----------
def main():
    connVol_1 = mdb.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database="vol_1",
        port=DB_CONFIG["port"],
        charset=DB_CONFIG["charset"],
        autocommit=True,
    )

    connVol = mdb.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database="vol",
        port=DB_CONFIG["port"],
        charset=DB_CONFIG["charset"],
        autocommit=True,
    )

    try:
        with connVol_1.cursor() as cursor:
            cursor.execute(SQL_DATES, (DATE_START, DATE_END))
            dates = [row[0] for row in cursor.fetchall()]

            for qd in dates:
                csv_path = export_one_date(cursor, qd)

                insertVolData(csv_path, connVol, 2000, False)

                if DELETE_CSV_AFTER_PROCESS:
                    csv_path.unlink()

                print(f"{qd}: completed")

    finally:
        connVol.close()
        connVol_1.close()

if __name__ == "__main__":
    main()