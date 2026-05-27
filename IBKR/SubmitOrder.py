from datetime import datetime

from ib_insync import MarketOrder
from IBKR.Logging import append_fill_row, update_commission, log
from IBKR.RequestMarketData import getLevelXpctFromIndex, getLargestLessThenOrEqualTo, buildOption
from IBKR.TradingCalendar import getMarketDateInFuture


def submitIBKROrder(ib, option, buySell, totalQuantity):
    order = MarketOrder(buySell, totalQuantity)  # or 'SELL'
    #trade = ib.placeOrder(option, order)
    trade = None
    return trade


def highest_strike_with_bid_leq(data, target_bid, targetStrike):
    highestStrike = targetStrike
    for _, _, strike, bid, _ in data:
        if bid is None:
            continue
        if bid <= target_bid and (strike > highestStrike):
            highestStrike = strike
    return highestStrike


def get_bid(data, strike, right=None):
    for _, r, k, bid, _ in data:
        if k == strike and (right is None or r == right):
            return bid
    return None  # not foun


def identifyOptionToTrade(spx_w_ExpiryStrikes, expiryTargetBusinessDaysAhead, expiryWindowIndays, spxPreviousClose, percentageChangeTargetForOptionStrike, optionType):
    dateXDaysAhead = getMarketDateInFuture(expiryTargetBusinessDaysAhead)  # remembering we are a day in front of CBOE
    # get closest expiryDate (SPXW only)
    sorted_expiries = sorted(spx_w_ExpiryStrikes.keys())
    expiryDateXDaysAhead = next((d for d in sorted_expiries if datetime.strptime(d, "%Y%m%d").date() >= dateXDaysAhead),
                                None)
    if expiryDateXDaysAhead is None:
        raise ValueError(f"No SPXW expiry on/after {dateXDaysAhead} within {expiryWindowIndays} days.")
    spxTargetLevel = getLevelXpctFromIndex(spxPreviousClose, percentageChangeTargetForOptionStrike)
    ## here we assume that only SPXW expiry is available
    putStrikes = sorted({r[2] for r in spx_w_ExpiryStrikes[expiryDateXDaysAhead] if r[1] == 'P'})
    targetStrike = getLargestLessThenOrEqualTo(putStrikes, spxTargetLevel)
    targetBid = get_bid(spx_w_ExpiryStrikes[expiryDateXDaysAhead], targetStrike)
    log(f"Initial taget strike was {targetStrike} with bid of {targetBid} ")
    ## identify the highest strike with a bid less than or equal to the bid of this strike
    targetStrike = highest_strike_with_bid_leq(spx_w_ExpiryStrikes[expiryDateXDaysAhead], targetBid, targetStrike)
    targetBid = get_bid(spx_w_ExpiryStrikes[expiryDateXDaysAhead], targetStrike)
    log(f"Final taget strike was {targetStrike} with bid of {targetBid} ")
    log(f"The target expiry {expiryDateXDaysAhead} is {expiryTargetBusinessDaysAhead} days ahead and the target strike that is {percentageChangeTargetForOptionStrike} away from yesterday's close {spxPreviousClose} is {targetStrike}")
    ## create order paraphernalia
    option = buildOption(expiryDateXDaysAhead, targetStrike, optionType, 'SPXW')
    return option

def createOrder(ib, option, isSubmitOrder, buySell, totalQuantity):
    qualified = ib.qualifyContracts(option)
    log(f"Qualified option: {qualified[0] if qualified else option}")
    # Create and submit a Market order
    trade = None
    if isSubmitOrder:
        trade = submitIBKROrder(ib, option, buySell, totalQuantity)
        # Append a row immediately on fill (no commission yet is OK)
        trade.fillEvent += lambda trd, fill: append_fill_row(fill)
        # When commission arrives, update that row
        trade.commissionReportEvent += lambda trd, fill, report: update_commission(
            fill.execution.execId,
            report.commission)
        # Wait until it is Filled / Cancelled / Inactive
        while trade.orderStatus.status not in ('Filled', 'Cancelled', 'Inactive'):
            ib.sleep(0.2)
    else:
        log("isSubmitOrder is False; built and qualified contract only (no order submitted).")

    if trade is not None:
        log(f"Final: {trade.orderStatus.status}; Filled: {trade.orderStatus.filled}")
    else:
        log("Final: no trade (isSubmitOrder was False).")

