from ib_insync import *
import pandas as pd
from datetime import datetime
import asyncio
import os

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# --------------------------------------------------
# Connect to IBKR
# --------------------------------------------------

ib = IB()
ib.connect("127.0.0.1", 7496, clientId=1)

positions = ib.positions()

if not positions:
    print("No positions found.")
    ib.disconnect()
    raise SystemExit

# --------------------------------------------------
# Subscribe to PnL for all positions
# --------------------------------------------------

pnl_subscriptions = {}

for pos in positions:
    pnl_subscriptions[pos.contract.conId] = ib.reqPnLSingle(
        pos.account,
        "",
        pos.contract.conId
    )

# --------------------------------------------------
# Wait for PnL updates
# --------------------------------------------------

def pnl_ready(pnl):
    return (
        pnl is not None
        and pnl.unrealizedPnL is not None
        and pnl.realizedPnL is not None
    )

timeout_seconds = 10
start = datetime.now()

while True:

    ready_count = sum(
        1
        for pnl in pnl_subscriptions.values()
        if pnl_ready(pnl)
    )

    print(
        f"PnL updates received: "
        f"{ready_count}/{len(pnl_subscriptions)}"
    )

    if ready_count == len(pnl_subscriptions):
        print("All PnL updates received.")
        break

    elapsed = (datetime.now() - start).total_seconds()

    if elapsed >= timeout_seconds:
        print("Timeout waiting for PnL updates.")
        break

    ib.sleep(0.5)

# --------------------------------------------------
# Gather position data
# --------------------------------------------------

rows = []

total_position = 0
total_position_cost = 0.0
total_market_value = 0.0
total_unrealized = 0.0
total_realized = 0.0

for pos in positions:

    contract = pos.contract

    # Snapshot market price
    ticker = ib.reqMktData(
        contract,
        "",
        snapshot=True
    )

    ib.sleep(1)

    market_price = ticker.marketPrice()

    if market_price is None or market_price <= 0:
        market_price = 0

    pnl = pnl_subscriptions.get(contract.conId)

    unrealized = (
        pnl.unrealizedPnL
        if pnl and pnl.unrealizedPnL is not None
        else 0
    )

    realized = (
        pnl.realizedPnL
        if pnl and pnl.realizedPnL is not None
        else 0
    )

    quantity = pos.position
    avg_cost = pos.avgCost

    position_cost = quantity * avg_cost
    market_value = quantity * market_price

    total_position += quantity
    total_position_cost += position_cost
    total_market_value += market_value
    total_unrealized += unrealized
    total_realized += realized

    rows.append({
        "Account": pos.account,
        "Symbol": contract.symbol,
        "SecType": contract.secType,
        "Currency": contract.currency,
        "Expiry": getattr(contract, "lastTradeDateOrContractMonth", ""),
        "Strike": getattr(contract, "strike", ""),
        "Right": getattr(contract, "right", ""),
        "Position": quantity,
        "AvgCost": round(avg_cost, 2),
        "PositionCost": round(position_cost, 2),
        "MarketPrice": round(market_price, 2),
        "MarketValue": round(market_value, 2),
        "UnrealizedPnL": round(unrealized, 2),
        "RealizedPnL": round(realized, 2)
    })

# --------------------------------------------------
# Export completion timestamp
# --------------------------------------------------

export_timestamp = datetime.now()
export_timestamp_str = export_timestamp.strftime("%Y-%m-%d %H:%M:%S")
run_date = export_timestamp.strftime("%Y-%m-%d")

# --------------------------------------------------
# Total row
# --------------------------------------------------

rows.append({
    "Account": "",
    "Symbol": "TOTAL",
    "SecType": "",
    "Currency": "",
    "Expiry": "",
    "Strike": "",
    "Right": "",
    "Position": total_position,
    "AvgCost": "",
    "PositionCost": round(total_position_cost, 2),
    "MarketPrice": "",
    "MarketValue": round(total_market_value, 2),
    "UnrealizedPnL": round(total_unrealized, 2),
    "RealizedPnL": round(total_realized, 2)
})

# --------------------------------------------------
# Create Positions DataFrame
# --------------------------------------------------

positions_df = pd.DataFrame(rows)

positions_df.insert(
    0,
    "ExportTimestamp",
    export_timestamp_str
)

# --------------------------------------------------
# Create Daily Summary DataFrame
# --------------------------------------------------

summary_df = pd.DataFrame([
    {
        "RunDate": run_date,
        "ExportTimestamp": export_timestamp_str,
        "OpenPositions": len(positions),
        "TotalSharesContracts": total_position,
        "PositionCost": round(total_position_cost, 2),
        "MarketValue": round(total_market_value, 2),
        "UnrealizedPnL": round(total_unrealized, 2),
        "RealizedPnL": round(total_realized, 2)
    }
])

# --------------------------------------------------
# Append / Create Excel Workbook
# --------------------------------------------------

filename = "IBKR_EOD_Positions.xlsx"

if os.path.exists(filename):

    existing_positions = pd.read_excel(
        filename,
        sheet_name="Positions"
    )

    existing_summary = pd.read_excel(
        filename,
        sheet_name="DailySummary"
    )

    positions_df = pd.concat(
        [existing_positions, positions_df],
        ignore_index=True
    )

    summary_df = pd.concat(
        [existing_summary, summary_df],
        ignore_index=True
    )

with pd.ExcelWriter(
    filename,
    engine="openpyxl",
    mode="w"
) as writer:

    positions_df.to_excel(
        writer,
        sheet_name="Positions",
        index=False
    )

    summary_df.to_excel(
        writer,
        sheet_name="DailySummary",
        index=False
    )

print(f"Export completed: {filename}")

# --------------------------------------------------
# Cleanup PnL subscriptions
# --------------------------------------------------

for pos in positions:
    ib.cancelPnLSingle(
        pos.account,
        "",
        pos.contract.conId
    )

ib.disconnect()