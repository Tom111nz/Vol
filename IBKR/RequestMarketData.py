import math
import os
from datetime import datetime, timedelta

import pandas as pd
from ib_insync import Index, IB

from IBKR.TradingCalendar import getMarketDateInFuture
from Logging import log


def sanity_check_market_data_type(ib: IB, spx: Index):
    """
    Best-effort sanity check: request a snapshot and read ticker.marketDataType.
    """
    try:
        t = ib.reqMktData(spx, snapshot=True)
        ib.sleep(1.0)
        return getattr(t, "marketDataType", None)
    except Exception:
        return None
## SPX Index
def createSpxIndex():
    return Index("SPX", "CBOE", "USD")

def getSpxSpot(ib: IB, getPreviousClose: bool):
    spx = createSpxIndex()
    ib.qualifyContracts(spx)

    #mdt = sanity_check_market_data_type(ib, spx)
    #log(f"Sanity check: ticker.marketDataType reported as {mdt}" if mdt is not None
    #    else "Sanity check: could not read ticker.marketDataType")
    try:
        [ticker] = ib.reqTickers(spx)
        if getPreviousClose:
            spot = ticker.close # previous close
        else:
            spot = ticker.marketPrice()
    except Exception:
        spot = None
    log(f"SPX spot: {' Exists' if spot is not None else ' N/A'}")
    return spot

## SPX Options
def pick_chain(chains, trading_class: str):
    """Pick chain by tradingClass ('SPX' or 'SPXW'), preferring SMART exchange if present."""
    candidates = [c for c in chains if getattr(c, "tradingClass", None) == trading_class]
    if not candidates:
        return None
    for c in candidates:
        if getattr(c, "exchange", None) == "SMART":
            return c
    return candidates[0]

def getSpxOptions(ib: IB):
    log("Requesting option chain definitions (reqSecDefOptParams) ...")
    spx = createSpxIndex()
    ib.qualifyContracts(spx)
    chains = ib.reqSecDefOptParams(spx.symbol, "", spx.secType, spx.conId)

    #chain_spx = pick_chain(chains, "SPX")
    chain_spxw = pick_chain(chains, "SPXW")

    return chain_spxw # chain_spx

## Output to CSV
def outPath(outputDirectory: str, filename: str) -> str:
    base = outputDirectory or os.getcwd()
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, filename)

def outputToCsv(directory: str, filename: str, data: list):
    outputFile = outPath(directory, filename)
    pd.DataFrame(data).to_csv(outputFile, index=False)
    log(f"Saved data to: {outputFile}")

## Select expiries
def parseExpiry_yyyymmdd(s: str):
    """Parse IB expiry string 'YYYYMMDD' into date. Return None if parsing fails."""
    try:
        return datetime.strptime(s, "%Y%m%d").date()
    except Exception:
        return None

def getExpiriesInWindow(chain, expiryWindowDays: int):

    today = getMarketDateInFuture(0) ## today is for CBOE (a day behind NZ)
    end = today + timedelta(days=expiryWindowDays)

    expiryList = getattr(chain, "expirations", []) or []

    keep = []
    for e in expiryList:
        d = parseExpiry_yyyymmdd(e)
        if d is None:
            continue
        if today <= d <= end:
            keep.append(e)
    return sorted(keep)

from ib_insync import Option

def validStrikesForExpiry_bidask(
    ib, expiry, chain,
    exchange='SMART', rights='P',
    lowerStrike=5000, upperStrike=9000,
    md_chunk=100
):
    """
    Fast bid/ask-only:
      1) ONE reqContractDetails call per expiry to get fully-qualified contracts
      2) Filter strikes locally
      3) Batch snapshot quotes with reqTickers in chunks
    """

    # Pattern contract: expiry + tradingClass/multiplier narrows results.
    # Leaving right='' lets IB return both calls & puts; we filter afterwards.
    pattern = Option(
        symbol='SPX',
        lastTradeDateOrContractMonth=expiry,
        strike=0.0,
        right='',
        exchange=exchange,
        currency='USD',
        tradingClass=chain.tradingClass,
        multiplier=chain.multiplier
    )

    cds = ib.reqContractDetails(pattern)  # one request, returns qualified contracts
    contracts = []
    for cd in cds:
        c = cd.contract
        if c.right != rights:
            continue
        if not (lowerStrike <= c.strike <= upperStrike):
            continue
        contracts.append(c)

    valid = []
    for i in range(0, len(contracts), md_chunk):
        chunk = contracts[i:i + md_chunk]
        tickers = ib.reqTickers(*chunk)  # snapshot quotes (fast) [2](https://www.reddit.com/r/algotrading/comments/ifmpem/looking_for_faster_ways_to_get_option_chains_from/)
        for t in tickers:
            valid.append((t.contract.strike, t.bid, t.ask))

    return valid


def getDictOfExpiryStrikes_bidask(ib, expiryList, chain, exchange, optionTypes,
                                  lowerStrike, upperStrike):
    out = {}
    for expiry in (expiryList or []):
        out[expiry] = validStrikesForExpiry_bidask(
            ib, expiry, chain, exchange, optionTypes, lowerStrike, upperStrike
        )
    return out

def validStrikesForExpiry(ib, expiry, chain, exchange='SMART', rights='P',
                          lowerStrike=5000, upperStrike=9000):

    valid = []
    # Build a batch of candidate option contracts (C and/or P) and qualify them.
    # Note: You can reduce the universe by filtering strikes (range, step, around spot, etc.)
    contracts = []
    for strike in chain.strikes:
        if not (lowerStrike <= strike <= upperStrike):
            continue  # skip to next iteration. Don't process strikes outside of band because is slow
        c = Option(
            symbol='SPX',
            lastTradeDateOrContractMonth=expiry,
            strike=float(strike),
            right=rights,
            exchange=exchange,
            currency='USD',
            tradingClass=chain.tradingClass,
            multiplier=chain.multiplier
        )
        contracts.append(c)

    # Qualify in chunks to avoid very large single messages
    CHUNK = 200
    for i in range(0, len(contracts), CHUNK):
        chunk = contracts[i:i+CHUNK]
        qualified = ib.qualifyContracts(*chunk)  # returns only the ones that are valid/qualified

        for qc in qualified:
            bid, ask, delta, gamma, vega, rho, impliedVol, optPrice, undPrice, ttm, expiryDateTime = requestBidAskandGreeks(ib, qc)
            valid.append((qc.strike, bid, ask))

    return valid

def getDictOfExpiryStrikes(ib, expiryList, chain, exchange, optionTypes, lowerStrike, upperStrike):
    dict = {}
    if expiryList is not None:
        for expiry in expiryList:
            dict[expiry] = validStrikesForExpiry(ib, expiry, chain, exchange, optionTypes, lowerStrike, upperStrike)
    return dict

def getLevelXpctFromIndex(indexLevel, percentMove):
    return indexLevel * (1 + percentMove)

def getLargestLessThenOrEqualTo(candidates: list, target):
        result = [x for x in candidates if x <= target]
        return max(result) if result else None

def buildOption(expiration, strike, optionType, chainType):
    return Option(
        symbol='SPX',
        lastTradeDateOrContractMonth=expiration,  # YYYYMMDD
        strike=strike,
        right=optionType,  # 'C' or 'P'
        exchange='SMART',  # or 'CBOE'
        currency='USD',
        tradingClass=chainType,  # 'SPX' or 'SPXW'
        multiplier='100'
    )


def has_value(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def years_to_expiry(option):
    expiry = datetime.strptime(
        option.lastTradeDateOrContractMonth,
        "%Y%m%d"
    ).replace(hour=16, minute=0, second=0) ## expiry is a date, we add the expiry time of 4pm

    now = datetime.now()

    return max(
        (expiry - now).total_seconds() /
        (365.25 * 24 * 3600),
        0
    ), expiry



def requestBidAskandGreeks(ib, option):
    #qualified = ib.qualifyContracts(option)
    #log(f"Qualified option: {qualified[0] if qualified else option}")
    ticker = ib.reqMktData(option)
    # Wait until we have bid/ask (or time out yourself)
    for _ in range(50):
        ib.sleep(0.1)
        if has_value(ticker.bid) and has_value(ticker.ask and ticker.modelGreeks is not None):
            break
    ttm, expiryDateTime = years_to_expiry(option)
    result = [ticker.bid, ticker.ask, ticker.modelGreeks.delta, ticker.modelGreeks.gamma,
              ticker.modelGreeks.vega, ticker.modelGreeks.theta, ticker.modelGreeks.rho, ticker.modelGreeks.impliedVol,
              ticker.modelGreeks.optPrice, ticker.modelGreeks.undPrice, ttm, expiryDateTime]
    ib.cancelMktData(option)
    return result
    #print("Bid/Ask:", ticker.bid, ticker.ask, "Sizes:", ticker.bidSize, ticker.askSize)
    ## If you want bid/ask derived Greeks (when available):
    #print("BidGreeks:", ticker.bidGreeks)
    #print("AskGreeks:", ticker.askGreeks) ## use this: buy greeks
    #print("LastGreeks:", ticker.lastGreeks)
    #print("ModelGreeks:", ticker.modelGreeks) ## more stable
    #print("ModelGreeks:ticker.marketDataType", ticker.marketDataType)
    ib.cancelMktData(option)