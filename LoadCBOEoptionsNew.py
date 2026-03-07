
import csv
import datetime as dt
import os

import pymysql
from dateutil.parser import parse
import pymysql as mdb

def insertVolData(csv_path, con, batch_size=2000, commit_every_batch=True):
    """
    Batched loader:
      - OptionExpiry + Strike resolved with caching (and inserted as needed).
      - Underlying/OptionGreeks/EoD inserted via executemany batches.
      - Commits per batch (default) or once per file.

    batch_size: 1000–5000 is a reasonable range for MySQL.
    """

    # ----------------------------
    # Helpers
    # ----------------------------
    def to_float(x):
        try:
            return float(x)
        except (ValueError, TypeError):
            return 0.0

    def norm_dt(s):  # keep your dateutil parse semantics, but normalize
        return parse(s).strftime("%Y-%m-%d %H:%M:%S")

    # ----------------------------
    # SQL
    # ----------------------------
    SQL_SEL_OPTIONEXPIRY = """
        SELECT ID
        FROM OptionExpiry
        WHERE quote_date=%s AND root=%s AND expiration=%s
    """
    SQL_INS_OPTIONEXPIRY = """
        INSERT INTO OptionExpiry (quote_date, root, expiration, rootOriginal, calendarTTE)
        VALUES (%s, %s, %s, %s, %s)
    """

    SQL_SEL_STRIKE = "SELECT ID FROM Strike WHERE strike=%s AND option_type=%s"
    SQL_INS_STRIKE = "INSERT INTO Strike (strike, option_type) VALUES (%s, %s)"

    # Underlying: one row per OptionExpiryID (recommended unique key on OptionExpiryID)
    SQL_UPSERT_UNDERLYING = """
        INSERT INTO Underlying (
            OptionExpiryID,
            underlying_bid_1545, underlying_ask_1545,
            implied_underlying_price_1545, active_underlying_price_1545,
            underlying_bid_eod, underlying_ask_eod
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            underlying_bid_1545 = VALUES(underlying_bid_1545),
            underlying_ask_1545 = VALUES(underlying_ask_1545),
            implied_underlying_price_1545 = VALUES(implied_underlying_price_1545),
            active_underlying_price_1545 = VALUES(active_underlying_price_1545),
            underlying_bid_eod = VALUES(underlying_bid_eod),
            underlying_ask_eod = VALUES(underlying_ask_eod)
    """

    # OptionGreeks: recommended unique key on (OptionExpiryID, StrikeID)
    SQL_UPSERT_OPTIONGREEKS = """
        INSERT INTO OptionGreeks (
            OptionExpiryID, StrikeID,
            bid_size_1545, bid_1545,
            ask_size_1545, ask_1545,
            implied_volatility_1545,
            delta_1545, gamma_1545, theta_1545, vega_1545, rho_1545
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            bid_size_1545 = VALUES(bid_size_1545),
            bid_1545      = VALUES(bid_1545),
            ask_size_1545 = VALUES(ask_size_1545),
            ask_1545      = VALUES(ask_1545),
            implied_volatility_1545 = VALUES(implied_volatility_1545),
            delta_1545 = VALUES(delta_1545),
            gamma_1545 = VALUES(gamma_1545),
            theta_1545 = VALUES(theta_1545),
            vega_1545  = VALUES(vega_1545),
            rho_1545   = VALUES(rho_1545)
    """

    # EoD: recommended unique key on (OptionExpiryID, StrikeID)
    SQL_UPSERT_EOD = """
        INSERT INTO EoD (
            OptionExpiryID, StrikeID,
            opn, high, low, clos,
            trade_volume,
            bid_size_eod, bid_eod,
            ask_size_eod, ask_eod,
            vwap, open_interest,
            delivery_code
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            opn = VALUES(opn),
            high = VALUES(high),
            low = VALUES(low),
            clos = VALUES(clos),
            trade_volume = VALUES(trade_volume),
            bid_size_eod = VALUES(bid_size_eod),
            bid_eod = VALUES(bid_eod),
            ask_size_eod = VALUES(ask_size_eod),
            ask_eod = VALUES(ask_eod),
            vwap = VALUES(vwap),
            open_interest = VALUES(open_interest),
            delivery_code = VALUES(delivery_code)
    """

    # ----------------------------
    # Caches (avoid repeated SELECTs)
    # ----------------------------
    option_expiry_cache = {}   # (quote_date, root, expiration) -> OptionExpiryID
    strike_cache = {}          # (strike, option_type) -> StrikeID
    underlying_seen = set()    # OptionExpiryID that we've queued/inserted Underlying for

    # ----------------------------
    # Batch buffers
    # ----------------------------
    underlying_batch = []
    greeks_batch = []
    eod_batch = []

    def flush(cur):
        """Flush batches using executemany() and optionally commit."""
        nonlocal underlying_batch, greeks_batch, eod_batch

        if underlying_batch:
            cur.executemany(SQL_UPSERT_UNDERLYING, underlying_batch)
            underlying_batch.clear()

        if greeks_batch:
            cur.executemany(SQL_UPSERT_OPTIONGREEKS, greeks_batch)
            greeks_batch.clear()

        if eod_batch:
            cur.executemany(SQL_UPSERT_EOD, eod_batch)
            eod_batch.clear()

        if commit_every_batch:
            con.commit()

    # ----------------------------
    # Main load
    # ----------------------------
    # Open with newline='' per csv docs (important on Windows). [4](https://stackoverflow.com/questions/12486623/paramiko-fails-to-download-large-files-1gb)
    with open(csv_path, newline="") as f, con.cursor() as cur:
        try:
            reader = csv.reader(f, delimiter=",")
            next(reader, None)  # skip header

            for row in reader:
                underlying_symbol = row[0]
                quote_date = row[1] + " 15:45:00"
                rootOriginal = row[2]
                expirationTemp = row[3]

                # Root/expiration time rules (your original logic)
                if rootOriginal == "SPX":
                    expiration = expirationTemp + " 08:30:00"
                    root = "SPX"
                elif rootOriginal == "SPXW":
                    expiration = expirationTemp + " 15:00:00"
                    root = "SPXW"
                elif rootOriginal == "VIX" or underlying_symbol == "^VIX":
                    expiration = expirationTemp + " 08:30:00"
                    root = "VIX"
                else:
                    expiration = expirationTemp + " 08:30:00"
                    root = "SPX"

                strike = row[4]
                option_type = row[5]

                opn = row[6]
                high = row[7]
                low = row[8]
                clos = row[9]
                trade_volume = row[10]

                bid_size_1545 = row[11]
                bid_1545 = row[12]
                ask_size_1545 = row[13]
                ask_1545 = row[14]

                underlying_bid_1545 = row[15]
                underlying_ask_1545 = row[16]
                implied_underlying_price_1545 = row[17]
                active_underlying_price_1545 = row[18]

                implied_volatility_1545 = row[19]
                delta_1545 = to_float(row[20])
                gamma_1545 = to_float(row[21])
                theta_1545 = to_float(row[22])
                vega_1545 = to_float(row[23])
                rho_1545 = to_float(row[24])

                bid_size_eod = row[25]
                bid_eod = row[26]
                ask_size_eod = row[27]
                ask_eod = row[28]
                underlying_bid_eod = row[29]
                underlying_ask_eod = row[30]
                vwap = to_float(row[31])
                open_interest = row[32]

                delivery_codeRaw = row[33]
                delivery_code = 0 if delivery_codeRaw == "" else delivery_codeRaw.replace("$", "")

                # calendarTTE
                exp_dt = dt.datetime.strptime(expiration, "%Y-%m-%d %H:%M:%S")
                q_dt = dt.datetime.strptime(quote_date, "%Y-%m-%d %H:%M:%S")
                calendarTTE = max((exp_dt - q_dt).total_seconds() / (60*60*24*365), 0)

                # ---- OptionExpiryID (cached) ----
                oe_key = (quote_date, root, expiration)
                OptionExpiryID = option_expiry_cache.get(oe_key)
                if OptionExpiryID is None:
                    cur.execute(SQL_SEL_OPTIONEXPIRY, (quote_date, root, expiration))
                    r = cur.fetchone()
                    if r:
                        OptionExpiryID = r[0]
                    else:
                        try:
                            cur.execute(SQL_INS_OPTIONEXPIRY, (
                                norm_dt(quote_date), root, norm_dt(expiration), rootOriginal, calendarTTE
                            ))
                            OptionExpiryID = cur.lastrowid  # id from auto-inc insert [5](https://pytutorial.com/fix-badzipfile-file-is-not-a-zip-file-in-python/)[6](https://docs.python.org/3/library/zipfile.html)
                        except pymysql.err.IntegrityError:
                            # Another run/process inserted it; re-select
                            cur.execute(SQL_SEL_OPTIONEXPIRY, (quote_date, root, expiration))
                            OptionExpiryID = cur.fetchone()[0]
                    option_expiry_cache[oe_key] = OptionExpiryID

                # ---- StrikeID (cached) ----
                s_key = (strike, option_type)
                StrikeID = strike_cache.get(s_key)
                if StrikeID is None:
                    cur.execute(SQL_SEL_STRIKE, (strike, option_type))
                    r = cur.fetchone()
                    if r:
                        StrikeID = r[0]
                    else:
                        try:
                            cur.execute(SQL_INS_STRIKE, (strike, option_type))
                            StrikeID = cur.lastrowid  # [5](https://pytutorial.com/fix-badzipfile-file-is-not-a-zip-file-in-python/)[6](https://docs.python.org/3/library/zipfile.html)
                        except pymysql.err.IntegrityError:
                            cur.execute(SQL_SEL_STRIKE, (strike, option_type))
                            StrikeID = cur.fetchone()[0]
                    strike_cache[s_key] = StrikeID

                # ---- Underlying (batch once per OptionExpiryID) ----
                # If Underlying has UNIQUE(OptionExpiryID), the UPSERT works as intended. [7](https://www.datachai.com/post/how-to-execute-sftp-file-transfers-using-python-and-paramiko)
                if OptionExpiryID not in underlying_seen:
                    underlying_seen.add(OptionExpiryID)
                    underlying_batch.append((
                        OptionExpiryID,
                        underlying_bid_1545, underlying_ask_1545,
                        implied_underlying_price_1545, active_underlying_price_1545,
                        underlying_bid_eod, underlying_ask_eod
                    ))

                # ---- OptionGreeks (batch) ----
                greeks_batch.append((
                    OptionExpiryID, StrikeID,
                    bid_size_1545, bid_1545,
                    ask_size_1545, ask_1545,
                    implied_volatility_1545,
                    delta_1545, gamma_1545, theta_1545, vega_1545, rho_1545
                ))

                # ---- EoD (batch) ----
                eod_batch.append((
                    OptionExpiryID, StrikeID,
                    opn, high, low, clos,
                    trade_volume,
                    bid_size_eod, bid_eod,
                    ask_size_eod, ask_eod,
                    vwap, open_interest,
                    delivery_code
                ))

                # Flush on batch boundary
                if len(greeks_batch) >= batch_size:
                    flush(cur)

            # final flush
            flush(cur)

            # If you chose commit_every_batch=False, commit once here.
            if not commit_every_batch:
                con.commit()

        except Exception:
            con.rollback()
            raise
