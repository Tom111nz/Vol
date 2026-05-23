from datetime import datetime

from ib_insync import LimitOrder, MarketOrder, Order

from IBKR.Connect import connect, quiet_errors
from IBKR.Logging import log, log_fill_to_csv, append_fill_row, update_commission
from IBKR.RequestMarketData import getSpxSpot, getSpxOptions, getExpiriesInWindow, validStrikesForExpiry, \
    getDictOfExpiryStrikes, getDateInFuture, getLevelXpctFromIndex, getLargestLessThenOrEqualTo, buildOption

reqMarketDataType = 3
expiryWindowIndays = 8
log(f"Connecting to IBKR with {reqMarketDataType}")
ib = connect(reqMarketDataType)
spxSpot = getSpxSpot(ib, False)
spxPreviousClose = getSpxSpot(ib, True)
log("SPX Index current: {spxPreviousClose}")
log("SPX Index yesterday's close: {spxPreviousClose}")
log("Get SPX and SPXW expiries in window of days: {expiryWindowIndays}")
chain_spx, chain_spxw = getSpxOptions(ib)
spxExpiriesInWindow = getExpiriesInWindow(chain_spx, expiryWindowIndays)
spx_w_ExpiriesInWindow = getExpiriesInWindow(chain_spxw, expiryWindowIndays)
log("Create dictionary of expiry and strikes")
spxExpiryStrikes = getDictOfExpiryStrikes(ib, spxExpiriesInWindow, chain_spx, "SMART", "P")
spx_w_ExpiryStrikes = getDictOfExpiryStrikes(ib, spx_w_ExpiriesInWindow, chain_spxw, "SMART", "P")
## SPX circuit breaks are at 7%, 13% and 20% (close for remainder of day) from previous day's close
## identify strike that is 5% down for front month (largest strike with ask of 0.05), and 7% down for day 2
dateXDaysAhead = getDateInFuture(1) # remembering we are a day in front of CBOE
expiryDateXDaysAhead = next((d for d in spx_w_ExpiryStrikes if datetime.strptime(d, "%Y%m%d") == dateXDaysAhead),None)
percentageChange = -0.07
xPctChgFromPreviousClose = getLevelXpctFromIndex(spx_w_ExpiryStrikes, percentageChange)
targetStrike = getLargestLessThenOrEqualTo(spx_w_ExpiryStrikes[expiryDateXDaysAhead], xPctChgFromPreviousClose)
log("The target expiry is {expiryDateXDaysAhead} and the target strike that is {percentageChange} away is {targetStrike}")
## create order
option = buildOption(expiryDateXDaysAhead, targetStrike, 'P', 'SPXW')
ib.qualifyContracts(option)

# Create and submit a Market order
order = MarketOrder('BUY', 1)   # or 'SELL'
trade = ib.placeOrder(option, order)

# Append a row immediately on fill (no commission yet is OK)
trade.fillEvent += lambda trd, fill: append_fill_row(fill)

# When commission arrives, update that row
trade.commissionReportEvent += lambda trd, fill, report: update_commission(
    fill.execution.execId,
    report.commission
)

# Wait until it is Filled / Cancelled / Inactive
while trade.orderStatus.status not in ('Filled', 'Cancelled', 'Inactive'):
    ib.sleep(0.2)

log("Final:" + trade.orderStatus.status + "; Filled:" + trade.orderStatus.filled)