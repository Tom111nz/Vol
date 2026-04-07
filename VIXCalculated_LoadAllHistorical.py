from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
from InterpolateUSYield import interpolateUSYield

import pymysql
import datetime
from dateutil.parser import parse

# ------------------------
# Database connection
# ------------------------
con = pymysql.connect(
    host="localhost",
    user="root",
    password="Bright1",
    db="Vol_Test",
    port=3306,
    autocommit=False,
    cursorclass=pymysql.cursors.DictCursor,
)

PRINT_RESULTS = False
USE_30_DAYS = False

# ------------------------
# Futures month mapping
# ------------------------
MONTH_MAP = {
    1: ("Z", "Dec"),
    2: ("F", "Jan"),
    3: ("G", "Feb"),
    4: ("H", "Mar"),
    5: ("J", "Apr"),
    6: ("K", "May"),
    7: ("M", "Jun"),
    8: ("N", "Jul"),
    9: ("Q", "Aug"),
    10: ("U", "Sep"),
    11: ("V", "Oct"),
    12: ("X", "Nov"),
}


def generate_vix_futures_string(expiry: datetime.datetime) -> str:
    code, month = MONTH_MAP[expiry.month]
    year = expiry.year - 2000
    return f"{code} ({month} {year:02d})"


# ------------------------
# Fetch all SPX expiries
# ------------------------
with con.cursor() as cur:
    cur.execute(
        """
        SELECT DISTINCT expiration
        FROM optionexpiry
        WHERE root = 'SPX'
        ORDER BY expiration
        """
    )
    expiries = [row["expiration"] for row in cur.fetchall()]

# ------------------------
# Pre-fetch existing VIXCalculated rows
# ------------------------
with con.cursor() as cur:
    cur.execute(
        """
        SELECT quote_date, FuturesContract, OptionExpiration
        FROM VIXCalculated
        """
    )
    existing_keys = {
        (row["quote_date"].date(), row["FuturesContract"], row["OptionExpiration"])
        for row in cur.fetchall()
    }

rows_to_insert = []

# ------------------------
# Main calculation loop
# ------------------------
with con.cursor() as cur:
    for option_expiry in expiries:
        expiry_date = option_expiry.date()
        futures_contract = generate_vix_futures_string(option_expiry)

        cur.execute(
            """
            SELECT
                oe.quote_date,
                und.underlying_bid_1545
            FROM OptionExpiry oe
            LEFT JOIN underlying und
                ON oe.id = und.optionexpiryid
            WHERE oe.root = 'SPX'
              AND oe.expiration = %s
            GROUP BY oe.quote_date, und.underlying_bid_1545
            ORDER BY oe.quote_date
            """,
            (option_expiry,),
        )

        for row in cur.fetchall():
            quote_date = row["quote_date"].date()

            if quote_date > expiry_date:
                continue

            key = (quote_date, futures_contract, option_expiry)
            if key in existing_keys:
                continue

            interest_rate = interpolateUSYield(
                row["quote_date"], option_expiry
            )

            vix_value = calculateVIXFromSingleExpiry(
                quote_date.strftime("%Y-%m-%d"),
                option_expiry.strftime("%Y-%m-%d %H:%M:%S"),
                interest_rate,
                PRINT_RESULTS,
                USE_30_DAYS,
            )

            rows_to_insert.append(
                (
                    quote_date,
                    futures_contract,
                    option_expiry,
                    interest_rate,
                    vix_value,
                )
            )

# ------------------------
# Batch insert
# ------------------------
if rows_to_insert:
    with con.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO VIXCalculated
            (
                quote_date,
                FuturesContract,
                OptionExpiration,
                InterestRateUsed,
                VIXCalculated
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            rows_to_insert,
        )

    con.commit()

print(f"Inserted {len(rows_to_insert)} VIXCalculated rows")
con.close()