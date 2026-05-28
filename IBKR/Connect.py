from ib_insync import IB
from Logging import log
import logging

import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

def quiet_errors(reqId, errorCode, errorString, contract):
    if errorCode in (200, 321):  # ignore invalid contract noise
        return
    print(f'Error {errorCode}: {errorString}')

def connect(reqMarketDataType: int):
    logging.getLogger('ib_insync').setLevel(logging.CRITICAL)
    logging.getLogger().setLevel(logging.CRITICAL)  # optional: root logger too

    ib = IB()
    ib.errorEvent.clear()
    ib.errorEvent += quiet_errors
    ib.RequestTimeout = 10
    ib.connect("127.0.0.1", 7496, clientId=11)
    ib.reqMarketDataType(reqMarketDataType)
    log(f"Requested market data type: {reqMarketDataType} (1=live,2=frozen,3=delayed,4=delayed-frozen)")
    return ib