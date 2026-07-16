from IBKR.Connect import connect
from IBKR.Logging import log
from IBKR.RequestMarketData import getSpxSpot, getSpxOptions, getExpiriesInWindow, \
    requestBidAskandGreeks, createSpxIndex, getDictOfExpiryStrikes_bidask
from IBKR.SubmitOrder import identifyOptionToTrade, createOrder
from IBKR.TradingCalendar import getMarketDateInFuture
from Constant import BUY
## SPXW expire at 4pm on the expiry day. We focus on using this options series.
##SPX expire on the open on a Friday having ceased trading the day before (Thursday 4pm)

def trade(reqMarketDataType, expiryTargetBusinessDaysAhead, percentageChangeTargetForOptionStrike,
          optionType, buySell, totalQuantity, isSubmitOrder, isLimitOrder):
    ## Parameters
    expiryWindowIndays = (getMarketDateInFuture(max(expiryTargetBusinessDaysAhead)) - getMarketDateInFuture(0)).days
    ##
    log(f"Connecting to IBKR with {reqMarketDataType}")
    ib = connect(reqMarketDataType)
    spxSpot = getSpxSpot(ib, False)
    spxPreviousClose = getSpxSpot(ib, True)
    log(f"SPX Index current: {spxSpot}")
    log(f"SPX Index yesterday's close: {spxPreviousClose}")
    log(f"Get SPXW expiries in window of days: {expiryWindowIndays}")
    chain_spxw = getSpxOptions(ib)
    #spxExpiriesInWindow = getExpiriesInWindow(chain_spx, expiryWindowIndays)
    spx_w_ExpiriesInWindow = getExpiriesInWindow(chain_spxw, expiryWindowIndays)
    log(f"Create dictionary of expiry and strikes")
    #spxExpiryStrikes = getDictOfExpiryStrikes(ib, spxExpiriesInWindow, chain_spx, "SMART", "P")
    ## calculate strike range to improve calculation speed
    lowerStrike = round((1 + min(percentageChangeTargetForOptionStrike)) * spxPreviousClose) - 200
    upperStrike = round((1 + max(percentageChangeTargetForOptionStrike)) * spxPreviousClose) + 200
    log(f"Lower strike: {lowerStrike} Upper strike: {upperStrike}")
    spx_w_ExpiryStrikes = getDictOfExpiryStrikes_bidask(ib, spx_w_ExpiriesInWindow, chain_spxw,
                                                 "SMART", "P", lowerStrike, upperStrike)
    log(f"Create order(s)")
    for index, quantity in enumerate(totalQuantity):
        log(f"Order {index}")
        option = identifyOptionToTrade(spx_w_ExpiryStrikes, expiryTargetBusinessDaysAhead[index],
                                       expiryWindowIndays, spxPreviousClose,
                                       percentageChangeTargetForOptionStrike[index], optionType[index])
        bid, ask, delta, gamma, vega, rho, impliedVol, optPrice, undPrice, ttm, expiryDateTime  = requestBidAskandGreeks(ib, option)
        createOrder(ib, option, isSubmitOrder, isLimitOrder, buySell[index], totalQuantity[index], ask if buySell[index] == BUY else bid)
    ib.cancelMktData(createSpxIndex())


if __name__ == "__main__":
    reqMarketDataType = 1
    expiryTargetBusinessDaysAhead = [1]  # this is based on CBOE dates (not NZ dates), so 0 is 0DTE expiry option
    percentageChangeTargetForOptionStrike = [-0.07]
    ## SPX circuit breaks are at 7%, 13% and 20% (close for remainder of day) from previous day's close
    optionType = ['P']
    buySell = [BUY]
    totalQuantity = [1]
    if reqMarketDataType == 1:
        isSubmitOrder = False
    else:
        isSubmitOrder = False
    isLimitOrder = True
    trade(reqMarketDataType, expiryTargetBusinessDaysAhead, percentageChangeTargetForOptionStrike,
          optionType, buySell, totalQuantity, isSubmitOrder, isLimitOrder)


