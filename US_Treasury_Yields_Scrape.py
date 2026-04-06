# Load US Treasury Daily Yield Curve into MySQL using XML feed
import datetime
import requests
import pymysql as mdb
import xml.etree.ElementTree as ET

# ----------------------------
# DB config
# ----------------------------
con = mdb.connect(
    host="localhost",
    user="root",
    passwd="Bright1",
    db="Vol_test",
    port=3306
)

# ----------------------------
# Helpers
# ----------------------------
def pct_to_decimal(x):
    if x is None:
        return None
    try:
        return float(x) / 100.0
    except ValueError:
        return None

# ----------------------------
# Get latest date in DB
# ----------------------------
cur = con.cursor()
cur.execute("SELECT MAX(quote_date) FROM USTreasuryYields")
latest = cur.fetchone()[0]
cur.close()

if latest is None:
    latest_dt = datetime.datetime(1900, 1, 1)
else:
    latest_dt = datetime.datetime.combine(latest, datetime.datetime.min.time())

print(f"Latest date in DB: {latest_dt.date()}")

# ----------------------------
# Dynamic years
# ----------------------------
start_year = latest_dt.year
end_year = datetime.datetime.today().year
years = list(range(start_year, end_year + 1))

print(f"Loading Treasury years: {years}")

# ----------------------------
# XML namespaces (from your file)
# ----------------------------
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
}

# ----------------------------
# Fetch + parse XML
# ----------------------------
rows = []

for year in years:
    url = (
        "https://home.treasury.gov/resource-center/data-chart-center/"
        "interest-rates/pages/xml"
        f"?data=daily_treasury_yield_curve&field_tdr_date_value={year}"
    )

    print(f"Fetching {year} XML...")
    r = requests.get(url, timeout=60)
    r.raise_for_status()

    root = ET.fromstring(r.text)

    for entry in root.findall("atom:entry", NS):
        props = entry.find("atom:content/m:properties", NS)
        if props is None:
            continue

        date_text = props.findtext("d:NEW_DATE", namespaces=NS)
        if not date_text:
            continue

        quote_date = datetime.datetime.fromisoformat(date_text[:10])

        if quote_date <= latest_dt:
            continue

        def val(tag):
            return pct_to_decimal(props.findtext(f"d:{tag}", namespaces=NS))

        rows.append((
            quote_date.strftime("%Y-%m-%d"),
            val("BC_1MONTH"),
            val("BC_2MONTH"),
            val("BC_3MONTH"),
            val("BC_6MONTH"),
            val("BC_1YEAR"),
            val("BC_2YEAR"),
            val("BC_3YEAR"),
            val("BC_5YEAR"),
            val("BC_7YEAR"),
            val("BC_10YEAR"),
            val("BC_20YEAR"),
            val("BC_30YEAR"),
        ))

# ----------------------------
# Insert into DB
# ----------------------------
rows.sort(key=lambda r: r[0])
print(f"Rows to insert: {len(rows)}")

insert_sql = """
INSERT IGNORE INTO USTreasuryYields
(`quote_date`, `1M`, `2M`, `3M`, `6M`, `1Y`, `2Y`, `3Y`, `5Y`, `7Y`, `10Y`, `20Y`, `30Y`)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

cur = con.cursor()
cur.executemany(insert_sql, rows)
con.commit()
cur.close()
con.close()

print("Treasury yield load complete.")