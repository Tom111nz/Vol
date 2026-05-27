from IBKR.Connect import connect
from IBKR.Logging import log
from IBKR.RequestMarketData import getSpxSpot, getSpxOptions, getExpiriesInWindow, getDictOfExpiryStrikes, \
    requestBidAskandGreeks, createSpxIndex
from IBKR.SubmitOrder import identifyOptionToTrade, createOrder

## SPXW expire at 4pm on the expiry day. We focus on using this options series.
##SPX expire on the open on a Friday having ceased trading the day before (Thursday 4pm)

## Parameters
reqMarketDataType = 1
expiryWindowIndays = 3
expiryTargetBusinessDaysAhead = [1, 0]
percentageChangeTargetForOptionStrike = [-0.07, -0.05]
## SPX circuit breaks are at 7%, 13% and 20% (close for remainder of day) from previous day's close
optionType = ['P', 'P']
buySell = ['BUY', 'BUY']
totalQuantity = [1, 1]
if reqMarketDataType == 1:
    isSubmitOrder = False
else: isSubmitOrder = False
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
## calculate strike range to improve calculation speed
lowerStrike = (1 + min(percentageChangeTargetForOptionStrike)) * spxPreviousClose - 200
upperStrike = (1 + max(percentageChangeTargetForOptionStrike)) * spxPreviousClose + 200
spx_w_ExpiryStrikes = getDictOfExpiryStrikes(ib, spx_w_ExpiriesInWindow, chain_spxw,
                                             "SMART", "P", lowerStrike, upperStrike)
### ORDERS ###
for index, quantity in enumerate(totalQuantity):
    log(f"Order {index}")
    option = identifyOptionToTrade(spx_w_ExpiryStrikes, expiryTargetBusinessDaysAhead[index],
                                   expiryWindowIndays, spxPreviousClose,
                                   percentageChangeTargetForOptionStrike[index], optionType[index])
    strike, bid, ask = requestBidAskandGreeks(ib, option)
    createOrder(ib, option, isSubmitOrder, buySell[index], totalQuantity[index])
### ORDER 2 ###
#log(f"Order 2")
#percentageChangeTargetForOptionStrike[1] = -0.05
#expiryTargetBusinessDaysAhead = 0 # remembering we are already a day in front of CBOE, so 1 -> 2days ahead
#buySell = 'BUY'
#totalQuantity = 1
#optionType = 'P'
#option = identifyOptionToTrade(spx_w_ExpiryStrikes, expiryTargetBusinessDaysAhead, expiryWindowIndays, spxPreviousClose, percentageChangeTargetForOptionStrike, optionType)
#requestBidAskandGreeks(ib, option)
#createOrder(ib, option, isSubmitOrder, buySell, totalQuantity)
ib.cancelMktData(createSpxIndex())