from datetime import datetime

from ib_insync import MarketOrder, LimitOrder
from IBKR.Logging import append_fill_row, update_commission, log
from IBKR.RequestMarketData import getLevelXpctFromIndex, getLargestLessThenOrEqualTo, buildOption
from IBKR.TradingCalendar import getMarketDateInFuture


def submitMarketOrder(ib, option, buySell, totalQuantity):
    order = MarketOrder(buySell, totalQuantity)  # or 'SELL'
    #trade = ib.placeOrder(option, order)
    trade = None
    return trade

def submitLimitOrder(ib, option, buySell, totalQuantity, price):
    order = LimitOrder(buySell, totalQuantity, price)  # or 'SELL'
    order.tif = 'DAY' ## active only for the trading day
    trade = ib.placeOrder(option, order)
    #trade = None
    return trade

def highest_strike_with_ask_leq(data, target_bid, targetStrike):
    highestStrike = targetStrike
    for strike, bid, ask in data:
        if ask is None:
            continue
        if ask <= target_bid and (strike > highestStrike):
            highestStrike = strike
    return highestStrike


def get_ask(data, strike):
    for k, bid, ask in data:
        if k == strike:
            return ask
    return None  # not found

def identifyOptionToTrade(spx_w_ExpiryStrikes, expiryTargetBusinessDaysAhead, expiryWindowIndays,
                          spxPreviousClose, percentageChangeTargetForOptionStrike, optionType):
    dateXDaysAhead = getMarketDateInFuture(expiryTargetBusinessDaysAhead)  # remembering we are a day in front of CBOE
    # get closest expiryDate (SPXW only)
    sorted_expiries = sorted(spx_w_ExpiryStrikes.keys())
    expiryDateXDaysAhead = next((d for d in sorted_expiries if datetime.strptime(d, "%Y%m%d").date() >= dateXDaysAhead),
                                None)
    if expiryDateXDaysAhead is None:
        raise ValueError(f"No SPXW expiry on/after {dateXDaysAhead} within {expiryWindowIndays} days.")
    spxTargetLevel = getLevelXpctFromIndex(spxPreviousClose, percentageChangeTargetForOptionStrike)
    ## here we assume that only SPXW expiry is available
    putStrikes = sorted({r[0] for r in spx_w_ExpiryStrikes[expiryDateXDaysAhead]})
    targetStrike = getLargestLessThenOrEqualTo(putStrikes, spxTargetLevel)
    targetAsk = get_ask(spx_w_ExpiryStrikes[expiryDateXDaysAhead], targetStrike)
    log(f"Initial taget strike was {targetStrike} with ask of {targetAsk} ")
    ## identify the highest strike with a bid less than or equal to the bid of this strike
    targetStrikeUpdated = highest_strike_with_ask_leq(spx_w_ExpiryStrikes[expiryDateXDaysAhead], targetAsk, targetStrike)
    targetAskUpdated = get_ask(spx_w_ExpiryStrikes[expiryDateXDaysAhead], targetStrikeUpdated)
    log(f"Updated taget strike was {targetStrikeUpdated} with ask of {targetAskUpdated} ")
    log(f"The target expiry {expiryDateXDaysAhead} is {expiryTargetBusinessDaysAhead} days ahead and the updated target strike that is {percentageChangeTargetForOptionStrike} away from yesterday's close {spxPreviousClose} is {targetStrikeUpdated}")
    ## create order paraphernalia
    option = buildOption(expiryDateXDaysAhead, targetStrikeUpdated, optionType, 'SPXW')
    return option

def createOrder(ib, option, isSubmitOrder, isLimitOrder, buySell, totalQuantity, price):
    qualified = ib.qualifyContracts(option)
    log(f"Qualified option: {qualified[0] if qualified else option}")
    # Create and submit a Market order
    trade = None
    if isSubmitOrder:
        if isLimitOrder:
            trade = submitLimitOrder(ib, option, buySell, totalQuantity, price)
            log(f"Submitted limit order: {trade}")
        else:
            trade = submitMarketOrder(ib, option, buySell, totalQuantity)
            log(f"Submitted market order: {trade}")
        # Wait until it is Filled / Cancelled / Inactive
        while trade.orderStatus.status not in ('Filled', 'Cancelled', 'Inactive'):
            ib.sleep(0.5)
        ib.sleep(0.5) # allow commission events to arrive
    else:
        log("isSubmitOrder is False; built and qualified contract only (no order submitted).")

    if trade is not None:
        log(f"Final: {trade.orderStatus.status}; Filled: {trade.orderStatus.filled}")
    else:
        log("Final: no trade (isSubmitOrder was False).")

