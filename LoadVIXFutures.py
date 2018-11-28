from __future__ import print_function
#from datetime import date, datetime, timedelta
import datetime
import csv
import requests
#import _mysql
#import MySQLdb as mdb
import pymysql as mdb
from dateutil.parser import parse
#import workdays
import dateutil
import sys
#from urllib.request import urlopen
#from bs4 import BeautifulSoup
import decimal
import numpy as np

global con
con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol", port = 3307)

def getVixFutureExpiry(futureDateCode):
    cur = con.cursor()
    sqlQuery = "select expiryDate from VIXFuturesExpiry where Contract = "'"%s"'"" % futureDateCode
    cur.execute(sqlQuery)
    res = cur.fetchone()
    cur.close()
    if res is None:
        return None
    else:
        return res[0]

contractExpiries = ['F', 'G', 'H', 'J', 'K', 'M', 'N', 'Q', 'U', 'V', 'X', 'Z']
contractExpiriesMonths = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

now = datetime.datetime.now()

## We go to the website and download the data for the rest of this year and for all of next year

thisYear = str(now.year)
VIXFutureList = list()

for i, mon in enumerate(contractExpiries[now.month -1:]):
    #aFile = 'http://cfe.cboe.com/Publish/ScheduledTask/MktData/datahouse/CFE_' + mon + thisYear[2:] + '_VX.csv'
    #print(mon + ' (' + contractExpiriesMonths[now.month -1+i] + ' ' + thisYear[2:] + ')')
    expiryDate = getVixFutureExpiry(mon + ' (' + contractExpiriesMonths[now.month -1+i] + ' ' + thisYear[2:] + ')')
    if expiryDate is None:
        break
    else:
        aFile = 'https://markets.cboe.com/us/futures/market_statistics/historical_data/products/csv/VX/' + str(expiryDate) #+ '/CFE_' + mon + thisYear[2:] + '_VX.csv'
    #print(aFile)
    #print('https://markets.cboe.com/us/futures/market_statistics/historical_data/products/csv/VX/2018-03-21/CFE_H18_VX.csv')
    #sys.exit(0)
    #https://markets.cboe.com/us/futures/market_statistics/historical_data/products/csv/VX/2018-04-18
        VIXFutureList.append(aFile)
nextYear = str(now.year + 1)
for i, mon in enumerate(contractExpiries):
    #aFile = 'http://cfe.cboe.com/Publish/ScheduledTask/MktData/datahouse/CFE_' + mon + nextYear[2:] + '_VX.csv'
    expiryDate = getVixFutureExpiry(mon + ' (' + contractExpiriesMonths[i] + ' ' + nextYear[2:] + ')')
    if expiryDate is None:
        break
    else:
        aFile = 'https://markets.cboe.com/us/futures/market_statistics/historical_data/products/csv/VX/' + str(expiryDate) #+ '/CFE_' + mon + thisYear[2:] + '_VX.csv'

        VIXFutureList.append(aFile)
        
        
## Holidays
Holidays = list()
Holidays.append(datetime.date(2016,1,1))
Holidays.append(datetime.date(2016,1,18))
Holidays.append(datetime.date(2016,2,15))
Holidays.append(datetime.date(2016,3,25))
Holidays.append(datetime.date(2016,5,30))
Holidays.append(datetime.date(2016,7,4))
Holidays.append(datetime.date(2016,9,5))
Holidays.append(datetime.date(2016,11,24))
Holidays.append(datetime.date(2016,12,26))

Holidays.append(datetime.date(2017,1,2))
Holidays.append(datetime.date(2017,1,16))
Holidays.append(datetime.date(2017,2,20))
Holidays.append(datetime.date(2017,4,14))
Holidays.append(datetime.date(2017,5,29))
Holidays.append(datetime.date(2017,7,4))
Holidays.append(datetime.date(2017,9,4))
Holidays.append(datetime.date(2017,11,23))
Holidays.append(datetime.date(2017,12,25))

Holidays.append(datetime.date(2018,1,1))
Holidays.append(datetime.date(2018,1,15)) ## Martin Luther
Holidays.append(datetime.date(2018,2,19)) ## Presidents
Holidays.append(datetime.date(2018,5,28)) ## Memorial
Holidays.append(datetime.date(2018,7,4))  ## Independence
Holidays.append(datetime.date(2018,9,3))  ## Labor
Holidays.append(datetime.date(2018,11,22))## Thankgiving
Holidays.append(datetime.date(2018,12,25))## Christmas

Holidays.append(datetime.date(2019,1,1))
Holidays.append(datetime.date(2019,1,21))
Holidays.append(datetime.date(2019,2,18))
Holidays.append(datetime.date(2019,5,27))
Holidays.append(datetime.date(2019,7,4))
Holidays.append(datetime.date(2019,9,2))
Holidays.append(datetime.date(2019,11,28))
Holidays.append(datetime.date(2019,12,25))

Holidays.append(datetime.date(2020,1,1))
Holidays.append(datetime.date(2020,1,20))
Holidays.append(datetime.date(2020,2,17))
Holidays.append(datetime.date(2020,5,25))
Holidays.append(datetime.date(2020,7,4))
Holidays.append(datetime.date(2020,9,7))
Holidays.append(datetime.date(2020,11,26))
Holidays.append(datetime.date(2020,12,25))

for v in VIXFutureList:
    with requests.Session() as s:
        try:
            download = s.get(v)
        except requests.exceptions.RequestException as e:
            print(v)
            print("Error1: Cannot get this file from CBOE webpage so we assume no subsequent files are available and we exit: 's%'" % v)
            sys.exit(0)
        decoded_content = download.content.decode('utf-8')#
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list()
        my_list = list(cr)
        print("Number of rows: " + str(my_list.__len__()))
        stringMeaningFileDoesNotExist = '<!DOCTYPE html PUBLIC'
        for row in my_list[0]:
            if stringMeaningFileDoesNotExist in row:
                print(row)
                print(v)
                print("Error2: This file does not exist on CBOE webpage so we assume no subsequent files are available and we exit")
                break
        BDInContract = my_list.__len__()
        BDCount = 0
        startRow = 1
        #print(v)
        #print(my_list[startRow])
        ## put in check for contract which has not expired
        firstRow = my_list[startRow]
        firstRowContract = str(firstRow[1]).replace(' 20', ' ') #28-Mar-18 due to data format change on cboe website
        #print(firstRowContract)
        cur = con.cursor()
        cur.execute("SELECT ExpiryDate from VIXFuturesExpiry where Contract = "'"%s"'"" % firstRowContract)
        rawExpiry = cur.fetchone()
        cur.close()
        if rawExpiry is None:
            print("No expiry in VIXFuturesExpiry for "'%s'": Go to http://www.cboe.com/delayedquote/futures-quotes ... ending this programme ..." % firstRowContract)
            break
        ExpiryDate = rawExpiry[0]
        lastRowTradeDate1 = dateutil.parser.parse(my_list[-1][0])
        lastRowTradeDate = lastRowTradeDate1.date()
##        print(ExpiryDate)
##        print(lastRowTradeDate)
##        print(firstRowContract)
        #sys.exit(0)
        ## check that the settle value is above zero:
##        for row in my_list[startRow:]:
##            if Decimal(row[5]) < 1.0:
##                print("1: Close is less than 1.0 for %s %s: %s", row[0], row[1], row[5])              
        ## compare the last Trade date with expiry date
        if lastRowTradeDate < ExpiryDate:
            ## this contract has not expired, so we work out the number of business days left ourselves
            #print("Contract "'%s'" has not expired yet!" % firstRowContract)
            for row in my_list[startRow:]:
                date = row[0]
                rowDateTemp = dateutil.parser.parse(date)
                rowDate = rowDateTemp.date()
                # calculate business days to expiry
                bizDays = np.busday_count(rowDate, ExpiryDate, [1,1,1,1,1,0,0], Holidays)
        
                BDCount += 1
                ## check whether row is in db
                cur = con.cursor()
                cur.execute("SELECT TradeDate from VIXFutures where Contract = "'"%s"'" and TradeDate = "'"%s"'"" % (firstRowContract, parse(date).strftime("%Y-%m-%d")))
                if cur.fetchone() is not None:
                    cur.close()
                    continue # data is already in database
                cur.close()
                try:
                    if decimal.Decimal(row[5]) < 1.0:
                        print("1: Not inserting. Close is less than 1.0 for %s %s: %s" % (str(row[0]), str(row[1]), str(row[5]))) 
                    else:
                        print("Inserting: '%s' and '%s'" % (firstRowContract, parse(date).strftime("%Y-%m-%d")))
                        cur = con.cursor()
                        cur.execute('''INSERT into VIXFutures (TradeDate, Contract, Opn, High, Low, Clos, Settle, Chnge, Volume, EFP, OI, BDToExpiry, CDToExpiry)
                              values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                              (parse(date).strftime("%Y-%m-%d %H:%M:%S"), row[1].replace(' 20', ' '), row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], str(bizDays), (ExpiryDate-rowDate).days))
                        con.commit()
                        cur.close()
                    
                except (mdb.Error, mdb.Warning) as e:
                    print(e)
                    print("1: Error for %s %s:", date, row[1])
        else:
            for row in my_list[startRow:]:
                date = row[0]
                rowDateTemp = dateutil.parser.parse(date)
                rowDate = rowDateTemp.date()
                BDCount += 1
                ## check whether row is already in db
                cur = con.cursor()
                cur.execute("SELECT TradeDate from VIXFutures where Contract = "'"%s"'" and TradeDate = "'"%s"'"" % (firstRowContract, parse(date).strftime("%Y-%m-%d")))
                if cur.fetchone() is not None:
                    cur.close()
                    continue # data is in database
                cur.close()
                try:
                    if decimal.Decimal(row[5]) < 1.0:
                        print("2: Not inserting. Close is less than 1.0 for %s %s: %s" % (str(row[0]), str(row[1]), str(row[5]))) 
                    else:
                        print("Inserting: '%s' and '%s'" % (firstRowContract, parse(date).strftime("%Y-%m-%d")))
                        cur = con.cursor()
                        cur.execute('''INSERT into VIXFutures (TradeDate, Contract, Opn, High, Low, Clos, Settle, Chnge, Volume, EFP, OI, BDToExpiry, CDToExpiry)
                              values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                              (parse(date).strftime("%Y-%m-%d %H:%M:%S"), row[1].replace(' 20', ' '), row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10], BDInContract-BDCount-startRow, (ExpiryDate-rowDate).days))
                        con.commit()
                        cur.close()
                    
                except (mdb.Error, mdb.Warning) as e:
                    print(e)
                    print("2: Error for %s %s:", date, row[1])
                
con.close()
