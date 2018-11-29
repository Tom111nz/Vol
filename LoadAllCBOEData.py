#!/usr/bin/env python3
## This file loads all the daily data from CBOE website
#import schedule
import time
#import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import datetime
import traceback
import pdb

def bugHunter(err):
    print(err)
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(err).__name__, err.args)
    print(message)
    print(traceback.format_exc())
    pdb.post_mortem()

def runAll():
    logging.basicConfig(filename='LoadAllCBOEData.log', level=logging.DEBUG)
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
            bugHunter(err)
#            print(Exception)
#            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
#            message = template.format(type(err).__name__, err.args)
#            print(message)
#            print(traceback.format_exc())
#            pdb.post_mortem()
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
            bugHunter(err)
            #print(Exception)
            print("Error in Loading VIX Futures Implied Rate but we carry on ....")
    logging.info('End VIX Futures Implied Rate') 
    ## SPX and VIX options
    print("(4) Loading SPX and VIX options")
    logging.info('Start SPX and VIX options')
    with open("Historical_CBOE_Download.py") as f:
        code = compile(f.read(), "Historical_CBOE_Download.py", 'exec')
        exec(code)   
    logging.info('End SPX and VIX options')
    ## Load US Treasury yields
    print("(5) Loading US Yields")
    logging.info('Start US Yields')
    with open("US_Treasury_Yields_Scrape.py") as f:
        code = compile(f.read(), "US_Treasury_Yields_Scrape.py", 'exec')
        exec(code)   
    logging.info('End US Yields')
    ## Calculate VIX
    print("(6) Calculate VIX")
    logging.info('Start Calculate VIX')
    with open("VIXCalculated.py") as f:
        code = compile(f.read(), "VIXCalculated.py", 'exec')
        exec(code)   
    logging.info('End Calculate VIX')
    ## check for new VIX futures
    print('check for new VIX futures')
    print('https://markets.cboe.com/us/futures/market_statistics/settlement/')
    nowEnd = datetime.datetime.now()
    logging.info('Program ended: %s' % nowEnd)

def my_listener(event):
    if event.exception:
        print('The job crashed :(')
    else:
        print('The job worked :)')

#if __name__ == '__main__':
#    sched = BackgroundScheduler()   #.scheduler.background.BackgroundScheduler()
#    sched.add_job(runAll, 'cron', day_of_week='tue-sun', hour=20, minute=10, jitter=60, misfire_grace_time=120) 
#    #sched.add_listener(my_listener)
#    sched.start()
#    try:
#        while True:
#            time.sleep(2)
#    except (KeyboardInterrupt, SystemExit):
#        sched.shutdown()
## to see details of jobs, run the following in the console at right: sched.print_jobs()
## to get job id run: sched.get_jobs()
## example of modifying the job: sched.modify_job("3acda0db27194eb7ab17c65c6996f610", max_instances=1)
    
## not used:
    #schedule.every().tuesday.at("22:00").do(runAll)
#schedule.every().wednesday.at("22:00").do(runAll)
#schedule.every().thursday.at("22:00").do(runAll)
#schedule.every().friday.at("22:00").do(runAll)
#schedule.every().saturday.at("22:00").do(runAll)
#schedule.every().tuesday.at("21:24").do(runAll)
#while True:
#    schedule.run_pending()
#    time.sleep(60) # wait one minute