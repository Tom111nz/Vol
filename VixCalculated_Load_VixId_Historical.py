import pymysql
import datetime

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

UPDATED_ROWS = 0

with con.cursor() as cur:
    # ------------------------------------------------------------
    # Fetch VIXCalculated rows needing VixOptionExpiryId update
    # ------------------------------------------------------------
    cur.execute(
        """
        SELECT
            OptionExpiryId,
            quote_date,
            OptionExpiration
        FROM VIXCalculated
        WHERE VixOptionExpiryId IS NULL
        ORDER BY quote_date, OptionExpiration
        """
    )

    rows = cur.fetchall()

    print(f"Found {len(rows)} rows to update")

    for row in rows:
        optionExpiryId = row["OptionExpiryId"]
        quote_date_dt = row["quote_date"]
        quote_date_str = quote_date_dt.strftime("%Y-%m-%d 15:45:00") ## match the quote_date in OptionExpiry table
        option_expiration_dt = row["OptionExpiration"]
        option_expiration_str = row["OptionExpiration"].strftime("%Y-%m-%d %H:%M:00")

        # ------------------------------------------------------------
        # Find best matching VIX option expiry
        # ------------------------------------------------------------
        cur.execute(
            """
            SELECT
                Id
            FROM optionexpiry
            WHERE root = 'VIX'
              AND quote_date = %s
              AND expiration = (SELECT MAX(v.expiration)
                 FROM optionexpiry v
                 WHERE v.root = 'VIX'
                AND v.expiration <= DATE_SUB(%s, INTERVAL 30 DAY)
                AND ABS(DATEDIFF(%s, v.expiration)) <= 35)
            """,
            (
                quote_date_str,
                option_expiration_str,
                option_expiration_str
            ),
        )

        vix_row = cur.fetchone()

        if not vix_row:
            # No suitable VIX expiry found — skip safely
            continue

        vix_option_expiry_id = vix_row["Id"]

        # ------------------------------------------------------------
        # Update VIXCalculated row
        # ------------------------------------------------------------
        cur.execute(
            """
            UPDATE VIXCalculated
            SET VixOptionExpiryId = %s
            WHERE OptionExpiryId = %s
            """,
            (vix_option_expiry_id, optionExpiryId),
        )
        #print(optionExpiryId, quote_date_str, option_expiration_str, vix_option_expiry_id)

        UPDATED_ROWS += 1

# ------------------------
# Commit updates
# ------------------------
con.commit()
con.close()

print(f"Updated {UPDATED_ROWS} VIXCalculated rows")