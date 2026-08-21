import yfinance as yf
from IBKR import Connect

# MySQL connection
con = Connect.get_db_connection()
cur = con.cursor()

# Get latest date already in the database
cur.execute("SELECT MAX(TradeDate) FROM spxdaily")
last_date = cur.fetchone()[0]

# First load vs incremental load
if last_date:
    start_date = last_date.strftime("%Y-%m-%d")
else:
    start_date = "1928-01-01"

# Download data
spx = yf.download(
    "^GSPC",
    start=start_date,
    progress=False,
    auto_adjust=False
)

spx.reset_index(inplace=True)

# Insert/Update records
sql = """
INSERT INTO spxdaily
(TradeDate, OpenPrice, HighPrice, LowPrice, ClosePrice, Volume)
VALUES (%s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    OpenPrice = VALUES(OpenPrice),
    HighPrice = VALUES(HighPrice),
    LowPrice = VALUES(LowPrice),
    ClosePrice = VALUES(ClosePrice),
    Volume = VALUES(Volume)
"""
spx.columns = [col[0] for col in spx.columns]

for _, row in spx.iterrows():
     cur.execute(sql, (
         row["Date"].date(),
         float(row["Open"]),
         float(row["High"]),
         float(row["Low"]),
         float(row["Close"]),
         int(row["Volume"])
     ))

con.commit()
cur.close()
con.close()

print(f"Processed {len(spx)} rows into SpxDaily.")