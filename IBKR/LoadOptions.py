from IBKR.Connect import connect
from IBKR.Logging import log
from IBKR.RequestMarketData import getSpxSpot, getSpxOptions, getExpiriesInWindow, getDictOfExpiryStrikes
from IBKR.SubmitOrder import identifyOptionToTrade, createOrder

## SPXW expire at 4pm on the expiry day. We focus on using this options series.
##SPX expire on the open on a Friday having ceased trading the day before (Thursday 4pm)

## Parameters
reqMarketDataType = 3
expiryWindowIndays = 8
isSubmitOrder = False
##
log(f"Connecting to IBKR with {reqMarketDataType}")
ib = connect(reqMarketDataType)
spxSpot = getSpxSpot(ib, False)
spxPreviousClose = getSpxSpot(ib, True)
log(f"SPX Index current: {spxSpot}")
log(f"SPX Index yesterday's close: {spxPreviousClose}")
log(f"Get SPX and SPXW expiries in window of days: {expiryWindowIndays}")
chain_spxw = getSpxOptions(ib)
#spxExpiriesInWindow = getExpiriesInWindow(chain_spx, expiryWindowIndays)
spx_w_ExpiriesInWindow = getExpiriesInWindow(chain_spxw, expiryWindowIndays)
log(f"Create dictionary of expiry and strikes")
#spxExpiryStrikes = getDictOfExpiryStrikes(ib, spxExpiriesInWindow, chain_spx, "SMART", "P")
spx_w_ExpiryStrikes = getDictOfExpiryStrikes(ib, spx_w_ExpiriesInWindow, chain_spxw, "SMART", "P")
## SPX circuit breaks are at 7%, 13% and 20% (close for remainder of day) from previous day's close
## identify strike that is 5% down for front month (largest strike with ask of 0.05), and 7% down for day 2
## ORDER 1
percentageChangeTargetForOptionStrike = -0.07
expiryTargetBusinessDaysAhead = 1 # remembering we are already a day in front of CBOE, so 1 -> 2days ahead
buySell = 'BUY'
totalQuantity = 1
optionType = 'P'
option = identifyOptionToTrade(spx_w_ExpiryStrikes, expiryTargetBusinessDaysAhead, expiryWindowIndays, spxPreviousClose, percentageChangeTargetForOptionStrike, optionType)
createOrder(ib, option, isSubmitOrder, buySell, totalQuantity)
## ORDER 2
percentageChangeTargetForOptionStrike = -0.05
expiryTargetBusinessDaysAhead = 0 # remembering we are already a day in front of CBOE, so 1 -> 2days ahead
buySell = 'BUY'
totalQuantity = 1
optionType = 'P'
option = identifyOptionToTrade(spx_w_ExpiryStrikes, expiryTargetBusinessDaysAhead, expiryWindowIndays, spxPreviousClose, percentageChangeTargetForOptionStrike, optionType)
createOrder(ib, option, isSubmitOrder, buySell, totalQuantity)