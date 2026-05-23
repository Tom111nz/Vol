import os
from datetime import datetime, timedelta

import pandas as pd
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.holiday import USFederalHolidayCalendar
from ib_insync import Index, IB, Option
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

    mdt = sanity_check_market_data_type(ib, spx)
    log(f"Sanity check: ticker.marketDataType reported as {mdt}" if mdt is not None
        else "Sanity check: could not read ticker.marketDataType")
    try:
        [ticker] = ib.reqTickers(spx)
        if getPreviousClose:
            spot = ticker.close # previous close
        else:
            spot = ticker.marketPrice()
    except Exception:
        spot = None
    log(f"SPX spot: {spot if spot is not None else 'N/A'}")
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

    chain_spx = pick_chain(chains, "SPX")
    chain_spxw = pick_chain(chains, "SPXW")

    return chain_spx, chain_spxw

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
    """
    Filter expirations to those within [today, today+EXPIRY_WINDOW_DAYS].
    expiry_list elements are 'YYYYMMDD' strings as returned by IB.
    """
    today = datetime.now().date()
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

def validStrikesForExpiry(ib, expiry, chain, exchange='SMART', rights=('C','P')):
    """
    expiry: 'YYYYMMDD'
    chain: one element from reqSecDefOptParams result (has tradingClass, multiplier, strikes)
    returns: sorted list of strikes that qualify for that expiry (at least one right qualifies)
    """
    valid = set()

    # Build a batch of candidate option contracts (C and/or P) and qualify them.
    # Note: You can reduce the universe by filtering strikes (range, step, around spot, etc.)
    contracts = []
    for strike in chain.strikes:
        for r in rights:
            c = Option(
                symbol='SPX',
                lastTradeDateOrContractMonth=expiry,
                strike=float(strike),
                right=r,
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
            valid.add(qc.strike)

    return sorted(valid)

def getDictOfExpiryStrikes(ib, expiryList, chain, exchange, optionTypes):
    dict = {}
    if expiryList is not None:
        for expiry in expiryList:
            dict[expiry] = validStrikesForExpiry(ib, expiry, chain, exchange, optionTypes)
    return dict

def getDateInFuture(daysInFuture: int):
    us_bd = CustomBusinessDay(calendar=USFederalHolidayCalendar())
    start = pd.Timestamp(datetime.today())
    result = start + daysInFuture * us_bd
    return result

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
