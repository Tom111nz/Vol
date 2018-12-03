#import MySQLdb as mdb
import pymysql as mdb
import sys
import datetime
from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
from InterpolateUSYield import interpolateUSYield
from GetDeltaThroughTime import getDeltaThroughTime
#from getDailyPnL import getDailyPnL
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import xlwt
from decimal import *

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol", port = 3307)

#deltaTargetList = [0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05]
deltaTargetList = [0.7]
printToFile = True
printToFileOptionRatio = True # if false prints usual graph
displayChart = False
calculateVIXFromSingleExpiry_PrintResults = False
# VIX Future Name, VIX Future Expiry, SPX Option Expiry
#VIXFutureOptionExpiryLists = [['X (Nov 10)','2010-11-17','2010-12-18']]
VIXFutureOptionExpiryLists = (
#('G (Feb 06)','2006-02-15','2006-03-18'), only has one data point
('H (Mar 06)','2006-03-22','2006-04-22'),
('J (Apr 06)','2006-04-19','2006-05-20'),
('K (May 06)','2006-05-17','2006-06-17'),
('M (Jun 06)','2006-06-21','2006-07-22'),
('N (Jul 06)','2006-07-19','2006-08-19'),
('Q (Aug 06)','2006-08-16','2006-09-16'),
('U (Sep 06)','2006-09-20','2006-10-21'),
('V (Oct 06)','2006-10-18','2006-11-18'),
('X (Nov 06)','2006-11-15','2006-12-16'),
('Z (Dec 06)','2006-12-20','2007-01-20'),
('F (Jan 07)','2007-01-17','2007-02-17'),
('G (Feb 07)','2007-02-14','2007-03-17'),
('H (Mar 07)','2007-03-21','2007-04-21'),
('J (Apr 07)','2007-04-18','2007-05-19'),
('K (May 07)','2007-05-16','2007-06-16'),
('M (Jun 07)','2007-06-20','2007-07-21'),
('N (Jul 07)','2007-07-18','2007-08-18'),
('Q (Aug 07)','2007-08-22','2007-09-22'),
('U (Sep 07)','2007-09-19','2007-10-20'),
('V (Oct 07)','2007-10-17','2007-11-17'),
('X (Nov 07)','2007-11-21','2007-12-22'),
('Z (Dec 07)','2007-12-19','2008-01-19'),
('F (Jan 08)','2008-01-16','2008-02-16'),
('G (Feb 08)','2008-02-19','2008-03-22'),
('H (Mar 08)','2008-03-19','2008-04-19'),
('J (Apr 08)','2008-04-16','2008-05-17'),
('K (May 08)','2008-05-21','2008-06-21'),
('M (Jun 08)','2008-06-18','2008-07-19'),
('N (Jul 08)','2008-07-16','2008-08-16'),
('Q (Aug 08)','2008-08-20','2008-09-20'),
('U (Sep 08)','2008-09-17','2008-10-18'),
('V (Oct 08)','2008-10-22','2008-11-22'),
('X (Nov 08)','2008-11-19','2008-12-20'),
('Z (Dec 08)','2008-12-17','2009-01-17'),
('F (Jan 09)','2009-01-21','2009-02-21'),
('G (Feb 09)','2009-02-18','2009-03-21'),
('H (Mar 09)','2009-03-18','2009-04-18'),
('J (Apr 09)','2009-04-15','2009-05-16'),
('K (May 09)','2009-05-20','2009-06-20'),
('M (Jun 09)','2009-06-17','2009-07-18'),
('N (Jul 09)','2009-07-22','2009-08-22'),
('Q (Aug 09)','2009-08-19','2009-09-19'),
('U (Sep 09)','2009-09-16','2009-10-17'),
('V (Oct 09)','2009-10-21','2009-11-21'),
('X (Nov 09)','2009-11-18','2009-12-19'),
('Z (Dec 09)','2009-12-16','2010-01-16'),
('F (Jan 10)','2010-01-20','2010-02-20'),
('G (Feb 10)','2010-02-17','2010-03-20'),
('H (Mar 10)','2010-03-17','2010-04-17'),
('J (Apr 10)','2010-04-21','2010-05-22'),
('K (May 10)','2010-05-19','2010-06-19'),
('M (Jun 10)','2010-06-16','2010-07-17'),
('N (Jul 10)','2010-07-21','2010-08-21'),
('Q (Aug 10)','2010-08-18','2010-09-18'),
('U (Sep 10)','2010-09-15','2010-10-16'),
('V (Oct 10)','2010-10-20','2010-11-20'),
('X (Nov 10)','2010-11-17','2010-12-18'),
('Z (Dec 10)','2010-12-22','2011-01-22'),
('F (Jan 11)','2011-01-19','2011-02-19'),
('G (Feb 11)','2011-02-16','2011-03-19'),
('H (Mar 11)','2011-03-16','2011-04-16'),
('J (Apr 11)','2011-04-20','2011-05-21'),
('K (May 11)','2011-05-18','2011-06-18'),
('M (Jun 11)','2011-06-15','2011-07-16'),
('N (Jul 11)','2011-07-20','2011-08-20'),
('Q (Aug 11)','2011-08-17','2011-09-17'),
('U (Sep 11)','2011-09-21','2011-10-22'),
('V (Oct 11)','2011-10-19','2011-11-19'),
('X (Nov 11)','2011-11-16','2011-12-17'),
('Z (Dec 11)','2011-12-21','2012-01-21'),
('F (Jan 12)','2012-01-18','2012-02-18'),
('G (Feb 12)','2012-02-15','2012-03-17'),
('H (Mar 12)','2012-03-21','2012-04-21'),
('J (Apr 12)','2012-04-18','2012-05-19'),
('K (May 12)','2012-05-16','2012-06-16'),
('M (Jun 12)','2012-06-20','2012-07-21'),
('N (Jul 12)','2012-07-18','2012-08-18'),
('Q (Aug 12)','2012-08-22','2012-09-22'),
('U (Sep 12)','2012-09-19','2012-10-20'),
('V (Oct 12)','2012-10-17','2012-11-17'),
('X (Nov 12)','2012-11-21','2012-12-22'),
('Z (Dec 12)','2012-12-19','2013-01-19'),
('F (Jan 13)','2013-01-16','2013-02-16'),
('G (Feb 13)','2013-02-13','2013-03-16'),
('H (Mar 13)','2013-03-20','2013-04-20'),
('J (Apr 13)','2013-04-17','2013-05-18'),
('K (May 13)','2013-05-22','2013-06-22'),
('M (Jun 13)','2013-06-19','2013-07-20'),
('N (Jul 13)','2013-07-17','2013-08-17'),
('Q (Aug 13)','2013-08-21','2013-09-21'),
('U (Sep 13)','2013-09-18','2013-10-19'),
('V (Oct 13)','2013-10-16','2013-11-16'),
('X (Nov 13)','2013-11-20','2013-12-21'),
('Z (Dec 13)','2013-12-18','2014-01-18'),
('F (Jan 14)','2014-01-22','2014-02-22'),
('G (Feb 14)','2014-02-19','2014-03-22'),
('H (Mar 14)','2014-03-18','2014-04-19'),
('J (Apr 14)','2014-04-16','2014-05-17'),
('K (May 14)','2014-05-21','2014-06-21'),
('M (Jun 14)','2014-06-18','2014-07-19'),
('N (Jul 14)','2014-07-16','2014-08-16'),
('Q (Aug 14)','2014-08-20','2014-09-20'),
('U (Sep 14)','2014-09-17','2014-10-18'),
('V (Oct 14)','2014-10-22','2014-11-22'),
('X (Nov 14)','2014-11-19','2014-12-20'),
('Z (Dec 14)','2014-12-17','2015-01-17'),
('F (Jan 15)','2015-01-21','2015-02-20'),
('G (Feb 15)','2015-02-18','2015-03-20'),
('H (Mar 15)','2015-03-18','2015-04-17'),
('J (Apr 15)','2015-04-15','2015-05-15'),
('K (May 15)','2015-05-20','2015-06-19'),
('M (Jun 15)','2015-06-17','2015-07-17'),
('N (Jul 15)','2015-07-22','2015-08-21'),
('Q (Aug 15)','2015-08-19','2015-09-18'),
('U (Sep 15)','2015-09-16','2015-10-16'),
('V (Oct 15)','2015-10-21','2015-11-20'),
('X (Nov 15)','2015-11-18','2015-12-19'),
('Z (Dec 15)','2015-12-16','2016-01-15'),
('F (Jan 16)','2016-01-20','2016-02-19'),
('G (Feb 16)','2016-02-17','2016-03-18'),
('H (Mar 16)','2016-03-16','2016-04-15'),
('J (Apr 16)','2016-04-20','2016-05-20'),
('K (May 16)','2016-05-18','2016-06-17'),
('M (Jun 16)','2016-06-15','2016-07-15'),
('N (Jul 16)','2016-07-20','2016-08-19'),
('Q (Aug 16)','2016-08-17','2016-09-16'),
('U (Sep 16)','2016-09-21','2016-10-21'),
('V (Oct 16)','2016-10-19','2016-11-18'),
('X (Nov 16)','2016-11-16','2016-12-16'),
('Z (Dec 16)','2016-12-21','2017-01-20'),
('F (Jan 17)','2017-01-18','2017-02-17'),
('G (Feb 17)','2017-02-15','2017-03-17'),
('H (Mar 17)','2017-03-22','2017-04-21'),
('J (Apr 17)','2017-04-19','2017-05-19'),
('K (May 17)','2017-05-17','2017-06-16'),
('M (Jun 17)','2017-06-21','2017-07-21'),
('N (Jul 17)','2017-07-19','2017-08-18'),
('Q (Aug 17)','2017-08-16','2017-09-15'),
('U (Sep 17)','2017-09-20','2017-10-20'),
('V (Oct 17)','2017-10-18','2017-11-17'),
('X (Nov 17)','2017-11-15','2017-12-15'),
('Z (Dec 17)','2017-12-20','2018-01-19'),
('F (Jan 18)','2018-01-17','2018-02-16'),
('G (Feb 18)','2018-02-14','2018-03-16'),
('H (Mar 18)','2018-03-21','2018-04-20'),
('J (Apr 18)','2018-04-18','2018-05-18'),
('K (May 18)','2018-05-16','2018-06-15'),
('M (Jun 18)','2018-06-20','2018-07-20'),
('N (Jul 18)','2018-07-18','2018-08-17'),
('Q (Aug 18)','2018-08-22','2018-09-21'),
('U (Sep 18)','2018-09-19','2018-10-19'),
('V (Oct 18)','2018-10-17','2018-11-16'),
('X (Nov 18)','2018-11-21','2018-12-21'),
('Z (Dec 18)','2018-12-19','2019-01-18'),
('F (Jan 19)','2019-01-16','2019-02-15'),
('G (Feb 19)','2019-02-13','2019-03-15'),
('H (Mar 19)','2019-03-19','2019-04-18'),
('J (Apr 19)','2019-04-17','2019-05-17'),
('K (May 19)','2019-05-22','2019-06-21')
)
#VIXFutureOptionExpiryLists = (('Q (Aug 17)','2017-08-16','2017-09-15'),('X (Nov 17)','2017-11-15','2017-12-15'), ('V (Oct 18)', '2018-10-17', '2018-11-16'))
#VIXFutureOptionExpiryLists = (('V (Oct 18)', '2018-10-17', '2018-11-16'),('Q (Aug 17)','2017-08-16','2017-09-15'),('X (Nov 17)','2017-11-15','2017-12-15'))

def getdeltaForStrikeAndExpiration(todayDate, expiration, optionType, strike):
    sqlQuery = ('select oe.quote_date, oe.Expiration, st.strike, st.option_type, og.delta_1545, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545, og.vega_1545 '
        'from optiongreeks og ' 
        'join optionexpiry oe on oe.ID = og.optionexpiryID '
        'join strike st on st.ID = og.strikeID '
        'where oe.ID in '
        '( '
        'select ID from optionexpiry where root in ("SPX") and expiration = '"'%s'"' and left(quote_date, 10) = '"'%s'"' '
        ') '
        'and st.option_type = '"'%s'"' '
        'and st.strike = %s ' 
        'order by oe.quote_date, oe.Expiration, st.strike;' % (expiration, todayDate, optionType, strike))
    #print(sqlQuery)
    cur = con.cursor()
    cur.execute(sqlQuery)
    strikeDataRaw = cur.fetchall()
    cur.close()
    if strikeDataRaw : # when strike == 0
        return strikeDataRaw[0]
    else:
        return [0,0,0,0,-0.3, 0, 0, 0, 0, 0] # to deal with if statement

now = datetime.datetime.now()
book = xlwt.Workbook()
# Loop through deltas
for deltaTarget in deltaTargetList:
    pp = PdfPages('Analytics_ActualYield_' + str(now.strftime("%Y-%m-%d")) + '_' + str(deltaTarget) + '.pdf') 
# Loop through VIX Futures
    for sheetNum, row in enumerate(VIXFutureOptionExpiryLists):
        
        futureName = row[0]
        futureExpiryString = row[1]
        futureExpiryDatetime = datetime.datetime.strptime(futureExpiryString, "%Y-%m-%d")
        optionExpiryString = row[2] + ' 08:30:00'
        optionExpiryDatetime = datetime.datetime.strptime(optionExpiryString, "%Y-%m-%d %H:%M:%S")

        sqlQuery = ('select oe.quote_date, und.underlying_bid_1545 from OptionExpiry oe '
                    'left join underlying und on oe.id = und.optionexpiryid '
                    'where oe.root = "SPX" '
                    'and oe.expiration = '"'%s'"' '
                    'group by oe.quote_date order by oe.quote_date;' % optionExpiryString)
        cur = con.cursor()
        cur.execute(sqlQuery)
        quoteDatesOptionsRaw = cur.fetchall()
        cur.close()
        # Now get actual VIXFuture close for each day (if possible)
        sqlQuery = ('select TradeDate, Settle from VIXFutures '
                    'where contract = '"'%s'"' '
                    'order by TradeDate asc;' % futureName)
        cur = con.cursor()
        cur.execute(sqlQuery)
        VIXFuturesDataRaw = cur.fetchall()
        cur.close()
        #print(sqlQuery)
        VIXFuturesDataRawDict = {}
        for row in VIXFuturesDataRaw:
            VIXFuturesDataRawDict[datetime.datetime.strftime(row[0], "%Y-%m-%d")] = row[1]
        # now get the VIX details for the period
        sqlQuery = ('select TradeDate, Opn, High, Low, Clos from VIX '
        'where tradeDate >= (select left(min(quote_date), 10) from optionexpiry where root in ("SPX") and expiration = '"'%s'"' ) ' % optionExpiryString)
        cur = con.cursor()
        cur.execute(sqlQuery)
        VIXDataRaw = cur.fetchall()
        cur.close()
        VIXDataRawDict = {}
        for row in VIXDataRaw:
            aList = list()
            aList.append(row[1])
            aList.append(row[2])
            aList.append(row[3])
            aList.append(row[4])
            VIXDataRawDict[datetime.datetime.strftime(row[0], "%Y-%m-%d")] = aList
        # Now get information on the strike nearest to the X delta each day
        if deltaTarget > 0.5:
            optionType = 'p'
        else:
            optionType = 'c'
        deltaXDict = getDeltaThroughTime(optionExpiryString, deltaTarget, optionType)

        ## Get the calculated VIX and put it in a dictionary
        sqlGetVIXCalculated = ('Select * from VIXCalculated where FuturesContract = '"'%s'"' and optionexpiration = '"'%s'"'' % (futureName, optionExpiryString))
        cur = con.cursor()
        cur.execute(sqlGetVIXCalculated)
        CalculatedVIXDataRaw = cur.fetchall()
        cur.close()
        CalculatedVIXDataRawDict = {}
        for row in CalculatedVIXDataRaw:
            CalculatedVIXDataRawDict[datetime.datetime.strftime(row[0], "%Y-%m-%d")] = row[4]
        
        # Now calculate VIX using optionExpiry for each day
        dailyValuesDict = {}
        
        #print('datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day) :' + str(datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day) ))
        for row in quoteDatesOptionsRaw:
            quoteDate = row[0]
            underlyingBid = row[1]
            #print(quoteDate)
            #print('datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) :' + str(datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) ))
            try:
                #optionExpiryDatetime = datetime.datetime.strptime(VIXAnalyticsClass.optionExpiryDate, "%Y-%m-%d %H:%M:%S")
                if datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) < datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day): 
                    quoteDateKey = datetime.datetime.strftime(quoteDate, "%Y-%m-%d")
                    iList = list()
                    if quoteDateKey in CalculatedVIXDataRawDict:
                        aVIX = CalculatedVIXDataRawDict[quoteDateKey]
                    else:
                        aVIX = 0.0
                    iList.append(aVIX)
                    iList.append(underlyingBid)
                    # add the VIX Futures data
                    if quoteDateKey in VIXFuturesDataRawDict:
                        VIXFuturesDataRawDay = VIXFuturesDataRawDict[quoteDateKey]
                         # scale VIX futures data from 23-Mar-2007 and earlier
                        if datetime.datetime.strptime(quoteDateKey, "%Y-%m-%d") <= datetime.datetime(2007, 3, 23):
                            iList.append(VIXFuturesDataRawDay/10)
                        else:
                            iList.append(VIXFuturesDataRawDay) # add the VIX futures settle for that day
                    else:
                        iList.append(0.0) # happens most frequently when VIX future has not yet started trading
                    # add the raw VIX data
                    if quoteDateKey in VIXDataRawDict:
                        vixList = VIXDataRawDict[quoteDateKey]
                        iList.append(vixList[0])
                        iList.append(vixList[1])
                        iList.append(vixList[2])
                        iList.append(vixList[3])
                    else:
                        iList.append(0)
                        iList.append(0)
                        iList.append(0)
                        iList.append(0)
                    # add the deltaXDict data
                    if quoteDateKey in deltaXDict:
                        deltaList = deltaXDict[quoteDateKey]
                        iList.append(deltaList[1])
                        iList.append(deltaList[2])
                        iList.append(deltaList[3])
                        iList.append(deltaList[4])
                        iList.append(deltaList[5])
                        iList.append(deltaList[6])
                        iList.append(deltaList[7])
                        iList.append(deltaList[8])
                        iList.append(deltaList[9])
                    else:
                        iList.append(0.0)
                        iList.append(0.0)
                        iList.append(0.0)
                        iList.append(0.0)
                        iList.append(0.0)
                        iList.append(0.0)
                        iList.append(0.0)
                        iList.append(0.0)
                        iList.append(0.0)
                    dailyValuesDict[quoteDateKey] = iList
                else:
                    print('skipping same date :' + optionExpiryString + " : " + str(datetime.datetime.strftime(row[0], "%Y-%m-%d")))
            except Exception as inst:
                print('error here')
                print(type(inst))    # the exception instance
                print(inst.args)     # arguments stored in .args
                print(inst)
                x, y = inst.args     # unpack args
                print('x =', x)
                print('y =', y)
    ##            print(str(datetime.datetime.strftime(row[0], "%Y-%m-%d")))
    ##            print(VIXAnalyticsClass.optionExpiryDate)
##        sortedKeys = sorted(dailyValuesDict.keys())
##        print(len(dailyValuesDict))
##        for row in sortedKeys:
##            print(row)
##            print(dailyValuesDict[row])
        

        ## The data we now have in dailyValuesDict is (key is date):
        ## [calculatedVIX, underling bid, VIX Future settle, Vix Opn, Vix High, Vix Low, Vix Clos,
        ## 'strike', 'option_type', 'delta', 'bid', 'ask', 'mid', 'imp_vol', 'vega', 'deltalessX']
        colHeaders = ['calculatedVIX', 'underling bid', 'VIX Future settle', 'Vix Opn', 'Vix High', 'Vix Low', 'Vix Clos',
        'strike', 'option_type', 'delta', 'bid', 'ask', 'mid', 'imp_vol', 'vega', 'deltalessX']
        dKey = {}
        for j in range(0, len(colHeaders)): # create numbering key for use below
            dKey[colHeaders[j]] = j
            #print(str(dKey[colHeaders[j]]) + '  ' + colHeaders[j])
        sortedKeys = sorted(dailyValuesDict.keys())
        dailyOptionPnlList = list()
        cumOptionPnl = list()
        dailyVixFuturePnlList = list()
        cumVixFuturePnl = list()
        dailyPnlList = list()
        cumDailyPnl = list()
        optionPosition = list()
        vixFuturePosition = list()
        optionTheo = list()
        dateList = list()
        calculatedVIX = list()
        underlingbid = list()
        VIXFuturesettle = list()
        VixOpn = list()
        VixHigh = list()
        VixLow = list()
        VixClos = list()
        strike = list()
        option_type = list()
        delta = list()
        bid = list()
        ask = list()
        bidActual = list()
        askActual = list()
        mid = list()
        imp_vol = list()
        imp_volActual = list()
        vega = list()
        vega_Actual = list()
        deltalessX = list()
        decisionList = list()
        dailyNaiveShortOptionPnlList = list()
        cumNaiveShortOptionPnL = list()
        strikeList = list()
        strikeDeltaList = list()
        underlyingBid = list()
        pnlDict = {}
        optionRatioList = list()
        newOptionAfterRatio = list()
        TTFEList = list()
        currentOptionPosition = 99 # to show we have no position
        optionPositionPerPoint = 100
        firstTimeThrough = True
        for u, row in enumerate(sortedKeys[1:]): # start at second row, we don't take position on first day of listing of option
            todayData = dailyValuesDict[row]
            if not todayData[dKey['VIX Future settle']] > 0: # we only start once the option has listed (the current loop) and the VIX future has listed
                continue
            yesterdayData = dailyValuesDict[sortedKeys[u]]
            # VIX Future Position
            if todayData[dKey['VIX Future settle']] > 0 and Decimal(todayData[dKey['calculatedVIX']]) - Decimal(todayData[dKey['VIX Future settle']]) < 0.5: ##
                currentVixFuturePosition = 1
            else:
                currentVixFuturePosition = 0
             ## add in cash position and margin require, and interest on margin
            
            if firstTimeThrough:
                if ((todayData[dKey['Vix High']] > 2 + todayData[dKey['VIX Future settle']]) or currentVixFuturePosition == 0):
                    currentOptionPosition = 0 # don't put on option position yet
                    if currentVixFuturePosition == 0:
                        decisionList.append('Not ready to open short position - currentVixFuturePosition is zero')
                    else: 
                        decisionList.append('Not ready to open short position - VIX related')
                else:
                    decisionList.append('Open short position')
                    currentOptionPosition = -1 # start with a short option position
                bidActual.append(todayData[dKey['bid']])
                askActual.append(todayData[dKey['ask']])
                dailyOptionTheo = todayData[dKey['bid']] # we sell at the bid
                currentStrike = todayData[dKey['strike']]
                currentStrikeDelta = todayData[dKey['delta']]
                dailyOptionPnl = (todayData[dKey['ask']] - todayData[dKey['bid']]) * currentOptionPosition * optionPositionPerPoint # pay the spread
                dailyNaiveShortOptionPnl = dailyOptionPnl
                imp_volActual.append(todayData[dKey['imp_vol']])
                vega_Actual.append(todayData[dKey['vega']])
            else:
                dailyNaiveShortOptionPnl = (todayData[dKey['ask']] - yesterdayData[dKey['ask']] ) * currentOptionPosition * optionPositionPerPoint
                #print('currentStrikeDetails: ' + str(row) + str(optionExpiryString) + str(optionType) + str(currentStrike))
                currentStrikeDetails = getdeltaForStrikeAndExpiration(row, optionExpiryString, optionType, currentStrike)
                #print(currentStrikeDetails)
                if ((optionPosition[-1] == -1 and (todayData[dKey['Vix High']] > 2 + todayData[dKey['VIX Future settle']])) or
                    (optionPosition[-1] == -1 and currentStrikeDetails[4] < -0.4) or
                    (optionPosition[-1] == -1 and currentStrikeDetails[4] > -0.1)): # criteria to close short, we buy back option at the ask
                    if (optionPosition[-1] == -1 and currentStrikeDetails[4] < -0.4):
                        decisionList.append('Close short position - large negative delta')
                    elif (optionPosition[-1] == -1 and currentStrikeDetails[4] > -0.1):
                        decisionList.append('Close short position - small negative delta')
                    else:
                        decisionList.append('Close short position - VIX related')
                    #dailyOptionTheo = todayData[dKey['ask']]                   
                    #currentStrikeDetails = getdeltaForStrikeAndExpiration(row, optionExpiryString, optionType, currentStrike)
                    dailyOptionTheo = currentStrikeDetails[6] # the ask
                    dailyOptionPnl = (dailyOptionTheo - askActual[-1]) * currentOptionPosition * optionPositionPerPoint
                    bidActual.append(currentStrikeDetails[5]) # the bid
                    askActual.append(currentStrikeDetails[6]) # the ask
                    imp_volActual.append(currentStrikeDetails[8])
                    vega_Actual.append(currentStrikeDetails[9])
                    currentOptionPosition = 0
                    currentStrike = 0
                    currentStrikeDelta = 0
                    ######### need a condition to put short option back on if Vix future has not started trading yet
                elif (optionPosition[-1] == 0 and todayData[dKey['Vix High']] < todayData[dKey['VIX Future settle']]): # criteria to put short back on [and todayData[dKey['VIX Future settle']] > 0]
                    decisionList.append('Reopen short position')
                    currentOptionPosition = -1
                    bidActual.append(todayData[dKey['bid']])
                    askActual.append(todayData[dKey['ask']])
                    dailyOptionTheo = todayData[dKey['bid']]
                    currentStrike = todayData[dKey['strike']]
                    currentStrikeDelta = todayData[dKey['delta']]
                    dailyOptionPnl = (todayData[dKey['ask']] - todayData[dKey['bid']]) * currentOptionPosition * optionPositionPerPoint # pay the spread
                    imp_volActual.append(todayData[dKey['imp_vol']])
                    vega_Actual.append(todayData[dKey['vega']])
                else: # keep current position (short or flat)
                    decisionList.append('Keep current position')
                    currentStrike = strikeList[-1]
                    ## work out what delta for strike is
                    if currentStrike == 0:
                        currentStrikeDelta = 0
                        dailyOptionTheo = 0
                        dailyOptionPnl = 0
                        bidActual.append(0)
                        askActual.append(0)
                        imp_volActual.append(0)
                        vega_Actual.append(0)
                    else:
                        currentStrikeDetails = getdeltaForStrikeAndExpiration(row, optionExpiryString, optionType, currentStrike)
                        #print(currentStrikeDetails)
                        currentStrikeDelta = Decimal(currentStrikeDetails[4])
                        dailyOptionTheo = currentStrikeDetails[6] # do we want this as an extra column, to isolate how naive strategy compares ?
                        dailyOptionPnl = (dailyOptionTheo - askActual[-1]) * currentOptionPosition * optionPositionPerPoint
                        bidActual.append(currentStrikeDetails[5]) # the bid
                        askActual.append(currentStrikeDetails[6]) # the ask
                        imp_volActual.append(currentStrikeDetails[8])
                        vega_Actual.append(currentStrikeDetails[9])
                
            # VIX Future PnL
            if firstTimeThrough: # on first day pnl is zero, if we buy vix future or not
                dailyVixFuturePnl = 0
                vixFuturePosition.append(currentVixFuturePosition)
            elif (vixFuturePosition[-1] == 0 and currentVixFuturePosition == 1): # buying the future some days after the options have listed
                dailyVixFuturePnl = 0
                vixFuturePosition.append(currentVixFuturePosition)
            else: # we've bought the VIX Future previously
                dailyVixFuturePnl = (Decimal(todayData[dKey['VIX Future settle']]) - Decimal(yesterdayData[dKey['VIX Future settle']])) * currentVixFuturePosition * 1000
                vixFuturePosition.append(currentVixFuturePosition)
            # Generics
            dailyPnl = Decimal(dailyOptionPnl) + Decimal(dailyVixFuturePnl)                 
            optionTheo.append(dailyOptionTheo)
            optionPosition.append(currentOptionPosition)
            #vixFuturePosition.append(currentVixFuturePosition)
            dailyOptionPnlList.append(dailyOptionPnl)
            dailyVixFuturePnlList.append(dailyVixFuturePnl)
            dailyPnlList.append(dailyPnl)
            dailyNaiveShortOptionPnlList.append(dailyNaiveShortOptionPnl)
            strikeList.append(currentStrike)
            strikeDeltaList.append(currentStrikeDelta)
            underlyingBid.append(todayData[dKey['underling bid']])
            TTFE = (futureExpiryDatetime - datetime.datetime.strptime(row, "%Y-%m-%d")).days / 365
            TTFEList.append(max(TTFE, 1/365))
            #print(str(TTFE) + ' ' + row)
            if todayData[dKey['ask']] > 0 and todayData[dKey['calculatedVIX']] > 0:
                optionRatio = max(math.pow(math.sqrt(TTFEList[-1]) * todayData[dKey['calculatedVIX']] / todayData[dKey['ask']], 2), sys.float_info.epsilon)
            else:
                optionRatio = sys.float_info.epsilon
            optionRatioList.append(optionRatio) # (sqrt(TTE) * calcVIX / 30d put theo)^2
            newOptionAfterRatio.append(todayData[dKey['ask']]/(math.sqrt(TTFEList[-1])/math.sqrt(optionRatioList[-1])))
            #print(newOptionAfterRatio[-1])
            if firstTimeThrough:
                cumOptionPnl.append(dailyOptionPnl)
                cumVixFuturePnl.append(dailyVixFuturePnl)
                cumDailyPnl.append(dailyPnl)
                cumNaiveShortOptionPnL.append(dailyNaiveShortOptionPnl)
            else:
                cumOptionPnl.append(dailyOptionPnl+ cumOptionPnl[-1])
                cumVixFuturePnl.append(dailyVixFuturePnl+cumVixFuturePnl[-1])
                cumDailyPnl.append(dailyPnl+cumDailyPnl[-1])
                cumNaiveShortOptionPnL.append(dailyNaiveShortOptionPnl+cumNaiveShortOptionPnL[-1])
            ## May have to put into lists the variables of interest ?
            dateList.append(row)
            calculatedVIX.append(todayData[dKey['calculatedVIX']])
            underlingbid.append(todayData[dKey['underling bid']])
            VIXFuturesettle.append(todayData[dKey['VIX Future settle']])
            VixOpn.append(todayData[dKey['Vix Opn']])
            VixHigh.append(todayData[dKey['Vix High']])
            VixLow.append(todayData[dKey['Vix Low']])
            VixClos.append(todayData[dKey['Vix Clos']])
            strike.append(todayData[dKey['strike']])
            option_type.append(todayData[dKey['option_type']])
            delta.append(todayData[dKey['delta']])
            bid.append(todayData[dKey['bid']])
            ask.append(todayData[dKey['ask']])
            mid.append(todayData[dKey['mid']])
            imp_vol.append(todayData[dKey['imp_vol']])
            vega.append(todayData[dKey['vega']])
            deltalessX.append(todayData[dKey['deltalessX']])
            firstTimeThrough = False
        ## 'strike', 'option_type', 'delta', 'bid', 'ask', 'mid', 'imp_vol', 'vega', 'deltalessX']
        
        #sheet1 =
        book.add_sheet(futureName)
        print('futureName: ' + futureName)
        #print('sheetNum: ' + str(sheetNum))
        listOfOutputsNames = ['Date', 'calculatedVIX', 'strike', 'strikeList', 'strikeDeltaList', 'underlyingBid', 'optionPosition', 'decisionList', 'optionTheo', 'bid Actual', 'ask Actual', 'bid 30d Put', 'ask 30d Put', 'imp_volActual', 'vega_Actual', 'vixFuturePosition', 'VIXFuturesettle', 'VixHigh', 'VixLow', 'VixClos', 'optionRatioList', 'TTFEList', 'dailyVixFuturePnlList', 'cumVixFuturePnl', 'dailyNaiveShortOptionPnlList', 'cumNaiveShortOptionPnL', 'dailyOptionPnlList', 'cumOptionPnl', 'dailyPnlList', 'cumDailyPnl']
        listOfOutputs = [dateList, calculatedVIX, strike, strikeList, strikeDeltaList, underlyingBid, optionPosition, decisionList, optionTheo, bidActual, askActual, bid, ask, imp_volActual, vega_Actual, vixFuturePosition, VIXFuturesettle, VixHigh, VixLow, VixClos, optionRatioList, TTFEList, dailyVixFuturePnlList, cumVixFuturePnl, dailyNaiveShortOptionPnlList, cumNaiveShortOptionPnL, dailyOptionPnlList, cumOptionPnl, dailyPnlList, cumDailyPnl]
        imp_volActual_100 = list()
        for arow in imp_volActual: # for graph
            imp_volActual_100.append(arow * 100)
        try:
            for outer in range(0, len(listOfOutputsNames)):
                book.get_sheet(sheetNum).write(0, outer, listOfOutputsNames[outer])
                for i,e in enumerate(listOfOutputs[outer]):
                    book.get_sheet(sheetNum).write(i+1,outer,e) # sheet1.write()
            
        except Exception as inst:
                print('error here')
                print(type(inst))    # the exception instance
                print(inst.args)     # arguments stored in .args
                print(inst)
        # print graph to pdf
        if printToFile:
            if printToFileOptionRatio:
                fig = plt.figure()
                ax = fig.add_subplot(111) 
                xAxis = range(len(calculatedVIX))
        ##                print('xAxis')
        ##                print(str(len(xAxis)))
                ax.plot(xAxis, calculatedVIX, 'r-', xAxis, VIXFuturesettle, 'g-', xAxis, imp_volActual_100, 'k--')
                axes = plt.gca()
                #axes.set_ylim([0,min(300, max(calculatedVIX)+20, max(VIXFuturesettle)+20)])
                ax2 = ax.twinx()
                ax2.plot(xAxis, optionRatioList, 'b-')#, strikeXD, 'r--')
                ax.legend(['Calculated VIX', 'VIX Future', '30d Put implied vol'], loc='best')
                #ax2.legend(['Underlying', 'Strike'], loc=3)
                plt.title(futureName)
            else:
                fig = plt.figure()
                ax = fig.add_subplot(111) 
                xAxis = range(len(calculatedVIX))
        ##                print('xAxis')
        ##                print(str(len(xAxis)))
                ax.plot(xAxis, calculatedVIX, 'r-', xAxis, VIXFuturesettle, 'g-', xAxis, imp_volActual_100, 'r--')
                axes = plt.gca()
                #axes.set_ylim([0,min(300, max(calculatedVIX)+20, max(VIXFuturesettle)+20)])
                ax2 = ax.twinx()
                ax2.plot(xAxis, underlyingBid, 'b--')#, strikeXD, 'r--')
                ax.legend(['Calculated VIX', 'VIX Future', '30d Put implied vol'], loc='best')
                #ax2.legend(['Underlying', 'Strike'], loc=3)
                plt.title(futureName)
            if displayChart:
                plt.show()
            if fig is not None:
                        #print(fig)
                pp.savefig(fig)
                plt.close()
            else:
                print('fig was none for ' + futureName)
            #print(fig)
book.save("PnL_" + now.strftime("%Y-%m-%d") + ".xls")
pp.close()
        ## Next job
        ## retain strike until need to re-hedge back to the actual 20d strike. Keep all columns and add new columns for the strike actually used (and its delta), and its theo.
        

        ## do we need to include the Vix Future margining (or just assume we fund 22k for life of deal)? Or even XSP option margin.
        ## http://cfe.cboe.com/framed/pdfframed?content=/publish/CFEMarginArchive/CFEMargins20180319.pdf&section=MARGINS&title=CFE+Margin+Update+-+March+19%2c+2018+%7c+Effective+-+March+21%2c+2018