from __future__ import print_function
from datetime import date, datetime, timedelta
import csv
import requests
import _mysql
import MySQLdb as mdb
from dateutil.parser import parse
import workdays
import datetime
import dateutil
import sys
from urllib.request import urlopen
from bs4 import BeautifulSoup
import math

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")

cur = con.cursor()
cur.execute("select * from vixfuturesexpiry where expirydate = '2017-08-16' order by expiryDate")
rawExpiry = cur.fetchall()
cur.close()

thirtyDaysInMinutes = 30*24*60
oneYearInMinutes = 365*24*60
timeScaler = thirtyDaysInMinutes / oneYearInMinutes

for row in rawExpiry:
    temp = row[1]
    tempS = temp.strftime('%m/%d/%Y')
    print(tempS)
    fileName = "VX_Series_" + tempS[:2] + tempS[3:5] + tempS[-4:] + ".csv"
    print(fileName)
    aFile = 'http://cfe.cboe.com/publish/CFEvixsettleseries/' + fileName
    with requests.Session() as s:
        try:
            download = s.get(aFile)
        except requests.exceptions.RequestException as e:
            print(v)
            print("Error1: Cannot get this file from CBOE webpage so we assume no subsequent files are available and we exit: 's%'" % v)
            sys.exit(0)
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list()
        my_list = list(cr)
        numRows = my_list.__len__()
        print("Number of rows: " + str(numRows))
        matrix = my_list[0:]
        rateList = list()
        for rowNew in range(2,numRows-1): # starting with row 2 means we ignore the header and first put (because is difficult to calculate delta_K)
            currentRow = matrix[rowNew]
            print(currentRow[3])
            letterP = "P"
            print(currentRow[3] == letterP)
            if currentRow[3] == letterP:
                nextRow = matrix[rowNew+1]
                previousRow = matrix[rowNew-1]
                contributionByStrike = float(currentRow[6])
                tradePrice = float(currentRow[4])
                strikeCalc = (0.5*(float(nextRow[2]) - float(previousRow[2])))/(math.pow(float(currentRow[2]), 2))
                rate = 1/timeScaler * (math.log(contributionByStrike/(tradePrice*strikeCalc)))
                rateList.append(rate)
            else:
                print(len(rateList))
                # calculate average, max and min, and then exit
                if len(rateList) > 0:
                    print("in Here")
                    maxRate = max(rateList)
                    minRate = min(rateList)
                    meanRate = sum(rateList) / len(rateList)
                    print(maxRate)
                    print(minRate)
                    print(meanRate)
                    # don't insert if difference is greater than 0.00005 ?
                    # put these values in the database. Add columns to VixFutureExpiry table and populate. Need to make initial SQL query dynamic (use current month?)
                    break
                
                

##now = datetime.datetime.now()
##
#### We go to the website and download the data for the rest of this year and for all of next year
##
##thisYear = str(now.year)
##VIXFutureList = list()
##print(contractExpiries[now.month -1:])
##
##for mon in contractExpiries[now.month -1:]:
##    aFile = 'http://cfe.cboe.com/Publish/ScheduledTask/MktData/datahouse/CFE_' + mon + thisYear[2:] + '_VX.csv'
##    VIXFutureList.append(aFile)
##nextYear = str(now.year + 1)
##for mon in contractExpiries:
##    aFile = 'http://cfe.cboe.com/Publish/ScheduledTask/MktData/datahouse/CFE_' + mon + nextYear[2:] + '_VX.csv'
##    VIXFutureList.append(aFile)
