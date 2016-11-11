## This file loads all the daily data from CBOE website

## Load VIX
print("Loading VIX")
with open("LoadVIX.py") as f:
    code = compile(f.read(), "LoadVIX.py", 'exec')
    exec(code)

## Load VIX Futures
print("Loading VIX Futures")
with open("LoadVIXFutures.py") as f:
    code = compile(f.read(), "LoadVIXFutures.py", 'exec')
    try:
        exec(code)
    except Exception as err:
        print(Exception)
        print("Error in Loading Vix Futures but we carry on ....")
            

## SPX and VIX options
print("Loading SPX and VIX options")
with open("Historical_CBOE_Download.py") as f:
    code = compile(f.read(), "Historical_CBOE_Download.py", 'exec')
    exec(code)   
