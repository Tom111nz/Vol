## This file loads all the daily data from CBOE website
import logging
import datetime
logging.basicConfig(filename='LoadAllCBOEData.log', level=logging.INFO)
now = datetime.datetime.now()
## Load VIX
print("(1) Loading VIX")
logging.info('Program started: %s' % now)
logging.info('Start VIX')
with open("LoadVIX.py") as f:
    code = compile(f.read(), "LoadVIX.py", 'exec')
    exec(code)
logging.info('End VIX')
## Load VIX Futures
print("(2) Loading VIX Futures")
logging.info('Start VIX Futures')
with open("LoadVIXFutures.py") as f:
    code = compile(f.read(), "LoadVIXFutures.py", 'exec')
    try:
        exec(code)
    except Exception as err:
        print(Exception)
        print("Error in Loading Vix Futures but we carry on ....")
logging.info('End VIX Futures')            
## Load VIX Future implied interest rate
print("(3) Loading VIX Futures Implied Rate")
logging.info('Start VIX Futures Implied Rate')
with open("LoadVIXFutureInterestRate.py") as f:
    code = compile(f.read(), "LoadVIXFutureInterestRate.py", 'exec')
    try:
        exec(code)
    except Exception as err:
        print(Exception)
        print("Error in Loading VIX Futures Implied Rate but we carry on ....")
logging.info('End VIX Futures Implied Rate') 
## SPX and VIX options
print("(4) Loading SPX and VIX options")
logging.info('Start SPX and VIX options')
with open("Historical_CBOE_Download.py") as f:
    code = compile(f.read(), "Historical_CBOE_Download.py", 'exec')
    exec(code)   
logging.info('End SPX and VIX options')
nowEnd = datetime.datetime.now()
logging.info('Program ended: %s' % nowEnd)
