#import MySQLdb as mdb
import pymysql as mdb
import datetime

def interpolateUSYield(quoteDateDateTime, optionExpiryDatetime):
    con = mdb.connect(host="localhost",user="root",
                      passwd="password",db="Vol", port = 3307)
    sqlQuery = ('select 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y from USTreasuryYields where quote_date = '"'%s'"';' % datetime.datetime.strftime(quoteDateDateTime, "%Y-%m-%d"))  
    cur = con.cursor()
    cur.execute(sqlQuery)
    sqlResults = cur.fetchall()
    cur.close()

    aMonth = 30.0/365.0
    TTEList = [aMonth, 3*aMonth, 6*aMonth, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0]
    yieldsList = sqlResults[0]
##    for row in sqlResults[0]:
##        print(row)
##    for row in TTEList:
##        print(row)
    calendarTTE = max(((optionExpiryDatetime - quoteDateDateTime).total_seconds())/(60*60*24*365), 0) # 365 days/year
##    print(calendarTTE)
    # find the first entry in the TTEList equal to or smaller than calendarTTE
    locAbove = next(x[0] for x in enumerate(TTEList) if x[1] >= calendarTTE)
    locBelow = locAbove - 1
    slope = (yieldsList[locAbove] - yieldsList[locBelow])/(TTEList[locAbove] - TTEList[locBelow])
    return yieldsList[locBelow] + slope * (calendarTTE - TTEList[locBelow])

##aYield = interpolateUSYield(datetime.date(2016, 12, 30), datetime.date(2017, 6, 30))
##print(aYield)
