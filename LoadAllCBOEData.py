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
import sys

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler('/Users/tomobrien/Git/Vol/CBOENewLogger.txt', mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger


""" Crontab
 https://superuser.com/questions/201172/mac-crontab-is-never-created
 Edit: crontab -e
 hit i
 then hit Esc
 type :wq to save
 01 20 * * 2-6 /Users/tomobrien/anaconda/bin/python /Users/tomobrien/Git/Vol/LoadAllCBOEData.py > /Users/tomobrien/Git/Vol/crontabLogging.log
 
 automate db backup
 mysqldump -uroot -p MyDatabase >/home/users/backup_MyDB/$(date +%F)_full_myDB.sql
****** Location of external drive is: /Volumes/"Seagate Expansion Drive"/Vol
"""
def bugHunter(err):
    print(err)
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(err).__name__, err.args)
    print(message)
    print(traceback.format_exc())
    pdb.post_mortem()

#def runAll():
#logging.basicConfig(filename='LoadAllCBOEData.log', level=logging.DEBUG)
logger = setup_custom_logger('myapp')
now = datetime.datetime.now()
## Load VIX 
print("(1) Loading VIX")
logger.info('Program started: %s' % now)
logger.info('Start VIX')
with open("/Users/tomobrien/Git/Vol/LoadVIX.py") as f:
    code = compile(f.read(), "LoadVIX.py", 'exec')
    exec(code)
logger.info('End VIX')
## Load VIX Futures
print("(2) Loading VIX Futures")
logger.info('Start VIX Futures')
with open("/Users/tomobrien/Git/Vol/LoadVIXFutures.py") as f:
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
logger.info('End VIX Futures')            
## Load VIX Future implied interest rate
print("(3) Loading VIX Futures Implied Rate")
logger.info('Start VIX Futures Implied Rate')
with open("/Users/tomobrien/Git/Vol/LoadVIXFutureInterestRate.py") as f:
    code = compile(f.read(), "LoadVIXFutureInterestRate.py", 'exec')
    try:
        exec(code)
    except Exception as err:
        bugHunter(err)
        #print(Exception)
        print("Error in Loading VIX Futures Implied Rate but we carry on ....")
logger.info('End VIX Futures Implied Rate') 
## SPX and VIX options
print("(4) Loading SPX and VIX options")
logger.info('Start SPX and VIX options')
with open("/Users/tomobrien/Git/Vol/Historical_CBOE_Download.py") as f:
    code = compile(f.read(), "Historical_CBOE_Download.py", 'exec')
    exec(code)   
logger.info('End SPX and VIX options')
## Load US Treasury yields
print("(5) Loading US Yields")
logger.info('Start US Yields')
with open("/Users/tomobrien/Git/Vol/US_Treasury_Yields_Scrape.py") as f:
    code = compile(f.read(), "US_Treasury_Yields_Scrape.py", 'exec')
    exec(code)   
logger.info('End US Yields')
## Calculate VIX
print("(6) Calculate VIX")
logger.info('Start Calculate VIX')
with open("/Users/tomobrien/Git/Vol/VIXCalculated.py") as f:
    code = compile(f.read(), "VIXCalculated.py", 'exec')
    exec(code)   
logger.info('End Calculate VIX')
## check for new VIX futures
print('check for new VIX futures')
print('https://markets.cboe.com/us/futures/market_statistics/settlement/')
nowEnd = datetime.datetime.now()
logger.info('Program ended: %s' % nowEnd)

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