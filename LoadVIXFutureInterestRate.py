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

thirtyDaysInMinutes = 30*24*60
oneYearInMinutes = 365*24*60
timeScaler = thirtyDaysInMinutes / oneYearInMinutes
now = datetime.datetime.now()
nowStr = now.strftime("%Y-%m-%d")

cur = con.cursor()
cur.execute("select * from VIXFuturesExpiry where impliedrate = -1 and expiryDate < " + nowStr + " order by expirydate desc")
rawExpiry = cur.fetchall()
cur.close()

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
        put_LetterP = matrix[2][3] # use whatever is the put designation ("P" or "Put")
        print("put_LetterP: " + str(put_LetterP))
        for rowNew in range(2,numRows-1): # starting with row 2 means we ignore the header and first put (because is difficult to calculate delta_K)
            currentRow = matrix[rowNew]
            nextRow = matrix[rowNew+1]
            previousRow = matrix[rowNew-1]
            if currentRow[3] == put_LetterP and nextRow[3] == put_LetterP:               
                contributionByStrike = float(currentRow[6])
                tradePrice = float(currentRow[4])
                strikeCalc = (0.5*(float(nextRow[2]) - float(previousRow[2])))/(math.pow(float(currentRow[2]), 2))
                rate = 1/timeScaler * (math.log(contributionByStrike/(tradePrice*strikeCalc)))
                rateList.append(rate)
            else:
                #print(len(rateList))
                # calculate average, max and min, and then exit
                if len(rateList) > 0:
                    maxRate = max(rateList)
                    minRate = min(rateList)
                    meanRate = sum(rateList) / len(rateList)
                    print(maxRate)
                    print(minRate)
                    print(meanRate)
                    # don't insert if difference is greater than 0.001 ?
                    if abs(maxRate - minRate) < 0.001:
                        print("update VIXFuturesExpiry set impliedrate = "'"%s"'"  where contract = "'"%s"'"" % (meanRate, row[0]))
                        cur = con.cursor()
                        cur.execute("update VIXFuturesExpiry set impliedrate = "'"%s"'"  where contract = "'"%s"'"" % (meanRate, row[0]))
                        con.commit()
                        cur.close()
                    else:
                        print("Difference between maxRate and minRate was "'"%s"'"  for "'"%s"'""  % (str(abs(maxRate - minRate)) , str(row[0])))
                        print("Tolerance is 0.001. No insert made to database. You need to fix this and work out why the difference between maxRate and minRate is so large")
                        for rowI in rateList:
                            print(rowI)
                    # put these values in the database. Add columns to VixFutureExpiry table and populate. Need to make initial SQL query dynamic (use current month?)
                    break
                else:
                    print("length of rateList is zero for "'"%s"'"" % str(row[0]))
                    print("No insert made to database. You need to fix this and work out why the length of rateList is zero")
