import yfinance as yf

# SPX ticker on Yahoo Finance
spx = yf.download("^GSPC", start="1928-01-01", end="2026-12-31")

print(spx.head())
print(spx.tail())

# Save to CSV if needed
spx.to_csv("spx_daily.csv")