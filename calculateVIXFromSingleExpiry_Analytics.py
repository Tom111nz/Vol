import MySQLdb as mdb
import sys
import datetime
from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")
print('hello')
class VIXAnalytics:
    def __init__(self, name, expiryDate):
        self.name = name
        self.vixFutureExpiryDate = datetime.datetime.strftime(expiryDate, "%Y-%m-%d %H:%M:%S")
        self.optionExpiryDate = datetime.datetime.strftime(datetime.datetime(expiryDate.year, expiryDate.month, expiryDate.day, 8, 30) + datetime.timedelta(days=30), "%Y-%m-%d %H:%M:%S")
        self.calculatedVIX = {} # a dictionary, with date as key and value will be a list holding two elements: calculated VIX and actual VIXFuture quotes for that date

# Get list of all VIXFutures
sqlQuery = 'select Contract, ExpiryDate from VIXFuturesExpiry group by ExpiryDate order by ExpiryDate'
cur = con.cursor()
cur.execute(sqlQuery)
allVIXFuturesAndTheirExpiries = cur.fetchall()
cur.close()

# Create classes
VIXFutureDict = {}
for row in allVIXFuturesAndTheirExpiries:
    VIXFutureDict[str(row[0])] = VIXAnalytics(row[0], row[1])
print('VIXFutureDict: ' + str(len(VIXFutureDict)))

# Loop through VIX Futures
for akey in VIXFutureDict.items():
    key = akey[0]
    #print('key: ' + key)
    VIXAnalyticsClass = VIXFutureDict[key]
    sqlQuery = ('select quote_date from OptionExpiry '
                'where rootOriginal = "SPX" '
                'and expiration = '"'%s'"' '
                'group by quote_date order by quote_date;' % VIXAnalyticsClass.optionExpiryDate)
    cur = con.cursor()
    cur.execute(sqlQuery)
    quoteDatesRaw = cur.fetchall()
    cur.close()
    # print(VIXAnalyticsClass.vixFutureExpiryDate + ":" + VIXAnalyticsClass.optionExpiryDate + ":" + str(len(quoteDatesRaw)))
    
    # Now calculate VIX using optionExpiryFor each day
    aDict = {}
    for row in quoteDatesRaw:
##        print('row:' + datetime.datetime.strftime(row[0], "%Y-%m-%d"))
##        print(VIXAnalyticsClass.optionExpiryDate)
        try:
            quoteDate = row[0]
            optionExpiryDatetime = datetime.datetime.strptime(VIXAnalyticsClass.optionExpiryDate, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) < datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day): 
                aDict[row[0]] = calculateVIXFromSingleExpiry(datetime.datetime.strftime(row[0], "%Y-%m-%d"), VIXAnalyticsClass.optionExpiryDate, 0.01, False)
            else:
                print('skipping same date :' + VIXAnalyticsClass.optionExpiryDate + " : " + str(datetime.datetime.strftime(row[0], "%Y-%m-%d")))
        except Exception as inst:
            print('error')
            print(str(datetime.datetime.strftime(row[0], "%Y-%m-%d")))
            print(VIXAnalyticsClass.optionExpiryDate)
    
    VIXFutureDict[key].calculatedVIX = aDict
    print("Done: " + key + " : " + str(len(aDict)))
    # Now get actual VIXFuture close for each day (if possible)
