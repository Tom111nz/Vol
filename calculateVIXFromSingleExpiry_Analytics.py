import MySQLdb as mdb
import sys
import datetime
from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
import matplotlib.pyplot as plt

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")

# VIX Future Name, VIX Future Expiry, SPX Option Expiry
VIXFutureOptionExpiryLists = (('J (Apr 10)','2010-04-21','2010-05-22'),('K (May 10)','2010-05-19','2010-06-19'),('M (Jun 10)','2010-06-16','2010-07-17'),('N (Jul 10)','2010-07-21','2010-08-21'),('Q (Aug 10)','2010-08-18','2010-09-18'),('U (Sep 10)','2010-09-15','2010-10-16'),('V (Oct 10)','2010-10-20','2010-11-20'),('X (Nov 10)','2010-11-17','2010-12-18'),('Z (Dec 10)','2010-12-22','2011-01-22'),('F (Jan 11)','2011-01-19','2011-02-19'),('G (Feb 11)','2011-02-16','2011-03-19'),('H (Mar 11)','2011-03-16','2011-04-16'),('J (Apr 11)','2011-04-20','2011-05-21'),('K (May 11)','2011-05-18','2011-06-18'),('M (Jun 11)','2011-06-15','2011-07-16'),('N (Jul 11)','2011-07-20','2011-08-20'),('Q (Aug 11)','2011-08-17','2011-09-17'),('U (Sep 11)','2011-09-21','2011-10-22'),('V (Oct 11)','2011-10-19','2011-11-19'),('X (Nov 11)','2011-11-16','2011-12-17'),('Z (Dec 11)','2011-12-21','2012-01-21'),('F (Jan 12)','2012-01-18','2012-02-18'),('G (Feb 12)','2012-02-15','2012-03-17'),('H (Mar 12)','2012-03-21','2012-04-21'),('J (Apr 12)','2012-04-18','2012-05-19'),('K (May 12)','2012-05-16','2012-06-16'),('M (Jun 12)','2012-06-20','2012-07-21'),('N (Jul 12)','2012-07-18','2012-08-18'),('Q (Aug 12)','2012-08-22','2012-09-22'),('U (Sep 12)','2012-09-19','2012-10-20'),('V (Oct 12)','2012-10-17','2012-11-17'),('X (Nov 12)','2012-11-21','2012-12-22'),('Z (Dec 12)','2012-12-19','2013-01-19'),('F (Jan 13)','2013-01-16','2013-02-16'),('G (Feb 13)','2013-02-13','2013-03-16'),('H (Mar 13)','2013-03-20','2013-04-20'),('J (Apr 13)','2013-04-17','2013-05-18'),('K (May 13)','2013-05-22','2013-06-22'),('M (Jun 13)','2013-06-19','2013-07-20'),('N (Jul 13)','2013-07-17','2013-08-17'),('Q (Aug 13)','2013-08-21','2013-09-21'),('U (Sep 13)','2013-09-18','2013-10-19'),('V (Oct 13)','2013-10-16','2013-11-16'),('X (Nov 13)','2013-11-20','2013-12-21'),('Z (Dec 13)','2013-12-18','2014-01-18'),('F (Jan 14)','2014-01-22','2014-02-22'),('G (Feb 14)','2014-02-19','2014-03-22'),('J (Apr 14)','2014-04-16','2014-05-17'),('K (May 14)','2014-05-21','2014-06-21'),('M (Jun 14)','2014-06-18','2014-07-19'),('N (Jul 14)','2014-07-16','2014-08-16'),('Q (Aug 14)','2014-08-20','2014-09-20'),('U (Sep 14)','2014-09-17','2014-10-18'),('V (Oct 14)','2014-10-22','2014-11-22'),('X (Nov 14)','2014-11-19','2014-12-20'),('Z (Dec 14)','2014-12-17','2015-01-17'),('F (Jan 15)','2015-01-21','2015-02-20'),('G (Feb 15)','2015-02-18','2015-03-20'),('H (Mar 15)','2015-03-18','2015-04-17'),('J (Apr 15)','2015-04-15','2015-05-15'),('K (May 15)','2015-05-20','2015-06-19'),('M (Jun 15)','2015-06-17','2015-07-17'),('N (Jul 15)','2015-07-22','2015-08-21'),('Q (Aug 15)','2015-08-19','2015-09-18'),('U (Sep 15)','2015-09-16','2015-10-16'),('V (Oct 15)','2015-10-21','2015-11-20'),('X (Nov 15)','2015-11-18','2015-12-19'),('Z (Dec 15)','2015-12-16','2016-01-15'),('F (Jan 16)','2016-01-20','2016-02-19'),('G (Feb 16)','2016-02-17','2016-03-18'),('H (Mar 16)','2016-03-16','2016-04-15'),('J (Apr 16)','2016-04-20','2016-05-20'),('K (May 16)','2016-05-18','2016-06-17'),('M (Jun 16)','2016-06-15','2016-07-15'),('N (Jul 16)','2016-07-20','2016-08-19'),('Q (Aug 16)','2016-08-17','2016-09-16'),('U (Sep 16)','2016-09-21','2016-10-21'),('V (Oct 16)','2016-10-19','2016-11-18'),('X (Nov 16)','2016-11-16','2016-12-16'),('Z (Dec 16)','2016-12-21','2017-01-20'),('F (Jan 17)','2017-01-18','2017-02-17'),('G (Feb 17)','2017-02-15','2017-03-17'),('H (Mar 17)','2017-03-22','2017-04-21'),('J (Apr 17)','2017-04-19','2017-05-19'),('K (May 17)','2017-05-17','2017-06-16'),('M (Jun 17)','2017-06-21','2017-07-21'),('N (Jul 17)','2017-07-19','2017-08-18'),('Q (Aug 17)','2017-08-16','2017-09-15'),('U (Sep 17)','2017-09-20','2017-10-20'),('V (Oct 17)','2017-10-18','2017-11-17'),('X (Nov 17)','2017-11-15','2017-12-15'),('Z (Dec 17)','2017-12-20','2018-01-19'))

##class VIXAnalytics:
##    def __init__(self, name, futureExpiryDate):
##        self.name = name
##        self.vixFutureExpiryDate = datetime.datetime.strftime(expiryDate, "%Y-%m-%d %H:%M:%S")
##        self.optionExpiryDate = datetime.datetime.strftime(datetime.datetime(expiryDate.year, expiryDate.month, expiryDate.day, 8, 30) + datetime.timedelta(days=30), "%Y-%m-%d %H:%M:%S")
##        self.calculatedVIX = {} # a dictionary, with date as key and value will be a list holding two elements: calculated VIX and actual VIXFuture quotes for that date

# Get list of all VIXFutures
##sqlQuery = 'select Contract, ExpiryDate from VIXFuturesExpiry group by ExpiryDate order by ExpiryDate'
##cur = con.cursor()
##cur.execute(sqlQuery)
##allVIXFuturesAndTheirExpiries = cur.fetchall()
##cur.close()

# Create classes
##VIXFutureDict = {}
##for row in allVIXFuturesAndTheirExpiries:
##    VIXFutureDict[str(row[0])] = VIXAnalytics(row[0], row[1])
##print('VIXFutureDict: ' + str(len(VIXFutureDict)))

# Loop through VIX Futures
for row in VIXFutureOptionExpiryLists:
    futureName = row[0]
    futureExpiryString = row[1]
    futureExpiryDatetime = datetime.datetime.strptime(futureExpiryString, "%Y-%m-%d")
    optionExpiryString = row[2] + ' 08:30:00'
    optionExpiryDatetime = datetime.datetime.strptime(optionExpiryString, "%Y-%m-%d %H:%M:%S")

##    VIXAnalyticsClass = VIXFutureDict[key]
    sqlQuery = ('select oe.quote_date, und.underlying_bid_1545 from OptionExpiry oe '
                'left join underlying und on oe.id = und.optionexpiryid '
                'where oe.rootOriginal = "SPX" '
                'and oe.expiration = '"'%s'"' '
                'group by oe.quote_date order by oe.quote_date;' % optionExpiryString)
    cur = con.cursor()
    cur.execute(sqlQuery)
    quoteDatesOptionsRaw = cur.fetchall()
    cur.close()
    # print(VIXAnalyticsClass.vixFutureExpiryDate + ":" + VIXAnalyticsClass.optionExpiryDate + ":" + str(len(quoteDatesRaw)))
    
    # Now calculate VIX using optionExpiry for each day
    dailyValuesDict = {}
    for row in quoteDatesOptionsRaw:
        quoteDate = row[0]
        underlyingBid = row[1]
        try:
            #optionExpiryDatetime = datetime.datetime.strptime(VIXAnalyticsClass.optionExpiryDate, "%Y-%m-%d %H:%M:%S")
            if datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) < datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day): 
                quoteDateKey = datetime.datetime.strftime(quoteDate, "%Y-%m-%d")
                iList = list()
                iList.append(calculateVIXFromSingleExpiry(quoteDateKey, optionExpiryString, 0.01, False))
                iList.append(underlyingBid)
                dailyValuesDict[quoteDateKey] = iList
            else:
                print('skipping same date :' + VIXAnalyticsClass.optionExpiryDate + " : " + str(datetime.datetime.strftime(row[0], "%Y-%m-%d")))
        except Exception as inst:
            tsar = 8
##            print('error')
##            print(str(datetime.datetime.strftime(row[0], "%Y-%m-%d")))
##            print(VIXAnalyticsClass.optionExpiryDate)
    
    #VIXFutureDict[key].calculatedVIX = aDict
    #print("Done: " + key + " : " + str(len(dailyValuesDict)))
            
    # Now get actual VIXFuture close for each day (if possible)
    sqlQuery = ('select TradeDate, Settle from VIXFutures '
                'where contract = '"'%s'"' '
                'order by TradeDate asc;' % futureName)
    cur = con.cursor()
    cur.execute(sqlQuery)
    VIXFuturesDataRaw = cur.fetchall()
    cur.close()
    #print('Check Key')
##    for keys, value in dailyValuesDict.items():
##        print('Key2: ' + str(keys))
    #print('Running VIXFuturesDataRaw')
    for row in VIXFuturesDataRaw:
        keyz = str(row[0])
        #print('keyz: ' + str(keyz))
        
        if keyz in dailyValuesDict:
            #print('############### found key!')
            aList = dailyValuesDict[keyz] # get the calculatedVIX and underlying bid for the day
            aList.append(row[1]) # add the VIX future for that day
            del dailyValuesDict[keyz]
            dailyValuesDict[keyz] = aList
        # if date (which is the key) not in dictionary, then ignore that date
        
    # Draw a graph
    # VIXFutureDict[key].calculatedVIX = dailyValuesDict

    # Graphs
    calcVixList = list()
    VIXFutureList = list()
    theDates = list()
    underlyingList = list()
    for keyx, value in dailyValuesDict.items():
        theDates.append(keyx)
        calcVixList.append(value[0])
        underlyingList.append(value[1])
        if len(value) > 2:
            VIXFutureList.append(value[2])
        else:
            VIXFutureList.append(0.0)
    # sort
    if len(calcVixList) > 1:
        iZipped = zip(theDates, calcVixList, VIXFutureList, underlyingList) # make sure everything is sorted by Date
        iZippedSorted = sorted(iZipped, key=lambda student: student[0])
        sortedTheDates = []
        sortedCalcVIXList = []
        sortedVIXFutureList = []
        sortedUnderlyingList = []
        for row in iZippedSorted:
            sortedTheDates.append(row[0])
            sortedCalcVIXList.append(row[1])
            sortedVIXFutureList.append(row[2])
            sortedUnderlyingList.append(row[3])
            
        fig = plt.figure()
        ax = fig.add_subplot(111)
        xAxis = range(len(sortedCalcVIXList))
        ax.plot(xAxis, sortedCalcVIXList, 'r^', xAxis, sortedVIXFutureList, 'g^')
        ax2 = ax.twinx()
        ax2.plot(xAxis, sortedUnderlyingList, 'b--')
        plt.title(futureName)
        plt.show()
##        for trow in sorted(theDates, key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d")):
##            print(trow)
    print('Done : ' + str(len(calcVixList)))
