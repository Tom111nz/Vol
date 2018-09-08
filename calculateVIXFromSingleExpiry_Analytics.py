import MySQLdb as mdb
import sys
import datetime
from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
from InterpolateUSYield import interpolateUSYield
from GetDeltaThroughTime import getDeltaThroughTime
from getDailyPnL import getDailyPnL
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import xlwt
from decimal import *

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")

#deltaTargetList = [0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05]
deltaTargetList = [0.7]
printToFile = True
calcVix = True
calculateVIXFromSingleExpiry_PrintResults = False
# VIX Future Name, VIX Future Expiry, SPX Option Expiry
#VIXFutureOptionExpiryLists = [['X (Nov 10)','2010-11-17','2010-12-18']]
VIXFutureOptionExpiryLists = (
#('G (Feb 06)','2006-02-15','2006-03-18'), only has one data point
##('H (Mar 06)','2006-03-22','2006-04-22'),
##('J (Apr 06)','2006-04-19','2006-05-20'),
##('K (May 06)','2006-05-17','2006-06-17'),
##('M (Jun 06)','2006-06-21','2006-07-22'),
##('N (Jul 06)','2006-07-19','2006-08-19'),
##('Q (Aug 06)','2006-08-16','2006-09-16'),
##('U (Sep 06)','2006-09-20','2006-10-21'),
##('V (Oct 06)','2006-10-18','2006-11-18'),
##('X (Nov 06)','2006-11-15','2006-12-16'),
##('Z (Dec 06)','2006-12-20','2007-01-20'),
##('F (Jan 07)','2007-01-17','2007-02-17'),
##('G (Feb 07)','2007-02-14','2007-03-17'),
##('H (Mar 07)','2007-03-21','2007-04-21'),
##('J (Apr 07)','2007-04-18','2007-05-19'),
##('K (May 07)','2007-05-16','2007-06-16'),
##('M (Jun 07)','2007-06-20','2007-07-21'),
##('N (Jul 07)','2007-07-18','2007-08-18'),
##('Q (Aug 07)','2007-08-22','2007-09-22'),
##('U (Sep 07)','2007-09-19','2007-10-20'),
##('V (Oct 07)','2007-10-17','2007-11-17'),
##('X (Nov 07)','2007-11-21','2007-12-22'),
##('Z (Dec 07)','2007-12-19','2008-01-19'),
##('F (Jan 08)','2008-01-16','2008-02-16'),
##('G (Feb 08)','2008-02-19','2008-03-22'),
##('H (Mar 08)','2008-03-19','2008-04-19'),
##('J (Apr 08)','2008-04-16','2008-05-17'),
##('K (May 08)','2008-05-21','2008-06-21'),
##('M (Jun 08)','2008-06-18','2008-07-19'),
##('N (Jul 08)','2008-07-16','2008-08-16'),
##('Q (Aug 08)','2008-08-20','2008-09-20'),
##('U (Sep 08)','2008-09-17','2008-10-18'),
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
('Z (Dec 17)','2017-12-20','2018-01-19')
)
VIXFutureOptionExpiryLists = (('Q (Aug 17)','2017-08-16','2017-09-15'),('X (Nov 17)','2017-11-15','2017-12-15'))

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

    ##    VIXAnalyticsClass = VIXFutureDict[key]
        sqlQuery = ('select oe.quote_date, und.underlying_bid_1545 from OptionExpiry oe '
                    'left join underlying und on oe.id = und.optionexpiryid '
                    'where oe.root = "SPX" '
                    'and oe.expiration = '"'%s'"' '
                    'group by oe.quote_date order by oe.quote_date;' % optionExpiryString)
        cur = con.cursor()
        cur.execute(sqlQuery)
        quoteDatesOptionsRaw = cur.fetchall()
        cur.close()
        print(sqlQuery)
        # Now get actual VIXFuture close for each day (if possible)
        sqlQuery = ('select TradeDate, Settle from VIXFutures '
                    'where contract = '"'%s'"' '
                    'order by TradeDate asc;' % futureName)
        cur = con.cursor()
        cur.execute(sqlQuery)
        VIXFuturesDataRaw = cur.fetchall()
        cur.close()
        print(sqlQuery)
        VIXFuturesDataRawDict = {}
        for row in VIXFuturesDataRaw:
            VIXFuturesDataRawDict[datetime.datetime.strftime(row[0], "%Y-%m-%d")] = row[1]
##        for i in VIXFuturesDataRawDict.keys():
##            print(str(i))
##            print(str(VIXFuturesDataRawDict[i]))
##            print(str(VIXFuturesDataRawDict['2016-11-21']))
##        sys.exit(0)
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
        
        print('datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day) :' + str(datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day) ))
        for row in quoteDatesOptionsRaw:
            quoteDate = row[0]
            underlyingBid = row[1]
            #print(quoteDate)
            #print('datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) :' + str(datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) ))
            try:
                #optionExpiryDatetime = datetime.datetime.strptime(VIXAnalyticsClass.optionExpiryDate, "%Y-%m-%d %H:%M:%S")
                if datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) < datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day): 
                    quoteDateKey = datetime.datetime.strftime(quoteDate, "%Y-%m-%d")
                    #quoteDateKey = '2009-06-25'
                    #print('quoteDateKey: ' + str(quoteDateKey))
                    iList = list()
                    if quoteDateKey in CalculatedVIXDataRawDict:
                        aVIX = CalculatedVIXDataRawDict[quoteDateKey]
                    else:
                        aVIX = 0.0
##                    if calcVix:
##                        try:
##                            interpolatedYield = interpolateUSYield(quoteDate, optionExpiryDatetime)
##                        except:
##                            interpolatedYield = 0.01
##                            print('Error: interpolatedYield = 0.01 ' + optionExpiryString + " : " + str(datetime.datetime.strftime(row[0], "%Y-%m-%d")))
##                        aVIX = calculateVIXFromSingleExpiry(quoteDateKey, optionExpiryString, interpolatedYield, calculateVIXFromSingleExpiry_PrintResults)
##                    else:
##                        aVIX = 0.0
                    iList.append(aVIX)
                    iList.append(underlyingBid)
                    # add the VIX Futures data
                    if quoteDateKey in VIXFuturesDataRawDict:
                        VIXFuturesDataRawDay = VIXFuturesDataRawDict[quoteDateKey]
                         # scale VIX futures data from 23-Mar-2007 and earlier
                        if datetime.datetime.strptime(quoteDateKey, "%Y-%m-%d") <= datetime.datetime(2007, 3, 23):
                            iList.append(VIXFuturesDataRawDay/10.0)
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
        mid = list()
        imp_vol = list()
        vega = list()
        deltalessX = list()
        decisionList = list()
        dailyNaiveShortOptionPnlList = list()
        cumNaiveShortOptionPnL = list()
        strikeList = list()
        strikeDeltaList = list()
        underlyingBid = list()
        pnlDict = {}
        currentOptionPosition = 99 # to show we have no position
        optionPositionPerPoint = 100
        for u, row in enumerate(sortedKeys[1:]): # start at second row, we don't take position on first day of listing of option
            todayData = dailyValuesDict[row]
            yesterdayData = dailyValuesDict[sortedKeys[u]]
             ## add in cash position and margin require, and interest on margin                          
            if u == 0:
                decisionList.append('Open short position')
                currentOptionPosition = -1 # start with a short option position
                dailyOptionTheo = todayData[dKey['bid']]
                currentStrike = todayData[dKey['strike']]
                currentStrikeDelta = todayData[dKey['delta']]
                dailyOptionPnl = (todayData[dKey['bid']] - todayData[dKey['ask']]) * currentOptionPosition * optionPositionPerPoint # pay the spread
                dailyNaiveShortOptionPnl = dailyOptionPnl
                
            else:
                dailyNaiveShortOptionPnl = (todayData[dKey['ask']] - yesterdayData[dKey['ask']] ) * currentOptionPosition * optionPositionPerPoint
                #print('currentStrikeDetails: ' + str(row) + str(optionExpiryString) + str(optionType) + str(currentStrike))
                currentStrikeDetails = getdeltaForStrikeAndExpiration(row, optionExpiryString, optionType, currentStrike)
                #print(currentStrikeDetails)
                if ((optionPosition[-1] == -1 and (todayData[dKey['Vix High']] > 2 + todayData[dKey['VIX Future settle']]) and todayData[dKey['VIX Future settle']] > 0) or
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
                    dailyOptionPnl = (dailyOptionTheo - optionTheo[-1]) * currentOptionPosition * optionPositionPerPoint
                    currentOptionPosition = 0
                    currentStrike = 0
                    currentStrikeDelta = 0
                    ######### need a condition to put short option back on if Vix future has not started trading yet
                elif (optionPosition[-1] == 0 and todayData[dKey['Vix High']] < todayData[dKey['calculatedVIX']]): # criteria to put short back on [and todayData[dKey['VIX Future settle']] > 0]
                    decisionList.append('Reopen short position')
                    currentOptionPosition = -1
                    dailyOptionTheo = todayData[dKey['bid']]
                    currentStrike = todayData[dKey['strike']]
                    currentStrikeDelta = todayData[dKey['delta']]
                    dailyOptionPnl = (todayData[dKey['bid']] - todayData[dKey['ask']]) * currentOptionPosition * optionPositionPerPoint # pay the spread
                else: # keep current position (short or flat)
                    decisionList.append('Keep current position')
                    currentStrike = strikeList[-1]
                    ## work out what delta for strike is
                    if currentStrike == 0:
                        currentStrikeDelta = 0
                        dailyOptionTheo = 0
                        dailyOptionPnl = 0
                    else:
                        currentStrikeDetails = getdeltaForStrikeAndExpiration(row, optionExpiryString, optionType, currentStrike)
                        #print(currentStrikeDetails)
                        currentStrikeDelta = Decimal(currentStrikeDetails[4])
                        dailyOptionTheo = currentStrikeDetails[6] # do we want this as an extra column, to isolate how naive strategy compares ?
                        dailyOptionPnl = (dailyOptionTheo - optionTheo[-1]) * currentOptionPosition * optionPositionPerPoint

            # VIX Future Position
            if todayData[dKey['VIX Future settle']] > 0:
                currentVixFuturePosition = 1
            else:
                currentVixFuturePosition = 0
            # VIX Future PnL
            if currentVixFuturePosition == 1 and vixFuturePosition[-1] == 0: # buying the future
                dailyVixFuturePnl = 0
            else:
                dailyVixFuturePnl = (Decimal(todayData[dKey['VIX Future settle']]) - Decimal(yesterdayData[dKey['VIX Future settle']])) * currentVixFuturePosition * 1000
            # Generics
            dailyPnl = Decimal(dailyOptionPnl) + Decimal(dailyVixFuturePnl)                 
            optionTheo.append(dailyOptionTheo)
            optionPosition.append(currentOptionPosition)
            vixFuturePosition.append(currentVixFuturePosition)
            dailyOptionPnlList.append(dailyOptionPnl)
            dailyVixFuturePnlList.append(dailyVixFuturePnl)
            dailyPnlList.append(dailyPnl)
            dailyNaiveShortOptionPnlList.append(dailyNaiveShortOptionPnl)
            strikeList.append(currentStrike)
            strikeDeltaList.append(currentStrikeDelta)
            underlyingBid.append(todayData[dKey['underling bid']])
            if u == 0:
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

        ## 'strike', 'option_type', 'delta', 'bid', 'ask', 'mid', 'imp_vol', 'vega', 'deltalessX']
        
        #sheet1 =
        book.add_sheet(futureName)
        print('futureName: ' + futureName)
        print('sheetNum: ' + str(sheetNum))
        listOfOutputsNames = ['Date', 'calculatedVIX', 'strike', 'strikeList', 'strikeDeltaList', 'underlyingBid', 'optionPosition', 'decisionList', 'optionTheo', 'bid', 'ask', 'vixFuturePosition', 'VIXFuturesettle', 'VixHigh', 'VixLow', 'VixClos', 'dailyVixFuturePnlList', 'cumVixFuturePnl', 'dailyNaiveShortOptionPnlList', 'cumNaiveShortOptionPnL', 'dailyOptionPnlList', 'cumOptionPnl', 'dailyPnlList', 'cumDailyPnl']
        listOfOutputs = [dateList, calculatedVIX, strike, strikeList, strikeDeltaList, underlyingBid, optionPosition, decisionList, optionTheo, bid, ask, vixFuturePosition, VIXFuturesettle, VixHigh, VixLow, VixClos, dailyVixFuturePnlList, cumVixFuturePnl, dailyNaiveShortOptionPnlList, cumNaiveShortOptionPnL, dailyOptionPnlList, cumOptionPnl, dailyPnlList, cumDailyPnl]
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
            fig = plt.figure()
            ax = fig.add_subplot(111) 
            xAxis = range(len(calculatedVIX))
    ##                print('xAxis')
    ##                print(str(len(xAxis)))
            ax.plot(xAxis, calculatedVIX, 'r-', xAxis, VIXFuturesettle, 'g-')
            axes = plt.gca()
            #axes.set_ylim([0,min(300, max(calculatedVIX)+20, max(VIXFuturesettle)+20)])
            ax2 = ax.twinx()
            ax2.plot(xAxis, underlyingBid, 'b--')#, strikeXD, 'r--')
            ax.legend(['Calculated VIX', 'VIX Future'], loc='best')
            #ax2.legend(['Underlying', 'Strike'], loc=3)
            plt.title(futureName)
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
        
        #sys.exit(0)
##        
####        counti = 0
####        for row in dailyValuesDict.items():
####            counti = counti + 1
####        print(futureName)
####        print('dailyValuesDict: ' + str(counti))
####        print('quoteDatesOptionsRaw: ' + str(len(quoteDatesOptionsRaw)))
##        
##        #VIXFutureDict[key].calculatedVIX = aDict
##        #print("Done: " + key + " : " + str(len(dailyValuesDict)))
##                
##
##        #print('Check Key')
##    ##    for keys, value in dailyValuesDict.items():
##    ##        print('Key2: ' + str(keys))
##        #print('Running VIXFuturesDataRaw')
####        for row in VIXFuturesDataRaw:
####            keyz = str(row[0])
####            #print('keyz: ' + str(keyz))
####            
####            if keyz in dailyValuesDict:
####                #print('############### found key!')
####                aList = dailyValuesDict[keyz] # get the calculatedVIX and underlying bid for the day
####                aList.append(row[1]) # add the VIX future settle for that day
####                del dailyValuesDict[keyz]
####                dailyValuesDict[keyz] = aList
####            # if date (which is the key) not in dictionary, then ignore that date
####            else:
####                print('Found date in VIX Future that is not in the corresponding options data: ' & keyz)
##
##        # Graphs
####        calcVixList = list()
####        VIXFutureList = list()
####        theDates = list()
####        underlyingList = list()
####        for keyx, value in dailyValuesDict.items():
####            theDates.append(keyx)
####            calcVixList.append(value[0])
####            underlyingList.append(value[1])
####            if len(value) > 2:
####                VIXFutureList.append(value[2])
####            else:
####                VIXFutureList.append(0.0) ## here we are just adding a value of zero for the VIX future, if no settle value exists (like when it has not started trading yet)
##        # sort
##        if len(calcVixList) > 1:
##            iZipped = zip(theDates, calcVixList, VIXFutureList, underlyingList) # make sure everything is sorted by Date
##            iZippedSorted = sorted(iZipped, key=lambda student: student[0])
##            sortedTheDates = []
##            sortedCalcVIXList = []
##            sortedVIXFutureList = []
##            sortedUnderlyingList = []
##            sortedVIXFutureListDict = {}
##            for row in iZippedSorted:
##                # scale VIX futures data from 23-Mar-2007 and earlier
##                if datetime.datetime.strptime(row[0], "%Y-%m-%d") <= datetime.datetime(2007, 3, 23):
##                    sortedVIXFutureList.append(row[2]/10)
##                else:
##                    sortedVIXFutureList.append(row[2])
##                sortedTheDates.append(row[0])
##                sortedCalcVIXList.append(row[1])               
##                sortedUnderlyingList.append(row[3])
##                sortedVIXFutureListDict[row[0]] = sortedVIXFutureList[-1] # need this for getDailyPnL
##
##            try:
##                # get X delta data
##                if deltaTarget > 0.5:
##                    optionType = 'p'
##                else:
##                    optionType = 'c'
##                deltaXDict = getDeltaThroughTime(optionExpiryString, deltaTarget, optionType)
####                print('deltaXDict')
####                for key, value in deltaXDict.items():
####                    print(key)
####                print('sortedtheDates')
####                for row in sortedTheDates:
####                    print(row)
##               # scale the 70D theos to the first Calculated VIX value
##        ##        print(sortedTheDates[0])
##        ##        print(deltaXDict)
##        ##        for key, value in deltaXDict.items():
##        ##                print(key)
##                #print('Here is key: ' + str(deltaXDict[sortedTheDates[0]]))
##                for x in range(0, len(sortedTheDates)):
##                    if str(sortedTheDates[x]) in deltaXDict:
####                        print('deltaXDict[sortedTheDates[0]][6]')
####                        print(str(deltaXDict[sortedTheDates[x]][6]))
##                        deltaXDFirst = deltaXDict[sortedTheDates[x]][6]
##                        break
##                    else:
##                        deltaXDict[sortedTheDates[x]] = [0, 0, 0, 0, 0, 0, 0] ## cannot find the date in deltaXDict, so add a zero for that date
##                        print('added a zero to deltaXDict for ' + str(sortedTheDates[x]))
####                        print('Major problem: first date not in deltaXDict')
####                        print('deltaXDict')
####                        for key, value in deltaXDict.items():
####                            print(key)
####                        print('dailyValuesDict')
####                        for key, value in dailyValuesDict.items():
####                            print(key)
####                        print('First date')
####                        print(sortedTheDates[0])
####                        sys.exit(0)
##                deltaXDScaled = []
##                deltaXDScaled_No = []
##                strikeXD = []
##                if deltaXDFirst == 0:
##                    print('deltaXDFirst is zero for ' + futureName + ' ' + str(deltaTarget))
##                    continue
##                # calculate the scaler
##                scale = 0
##                for numb in sortedCalcVIXList:
##                    if numb > 0:
##                        scale = numb / deltaXDFirst
##                        break
####                print('scale:'  + str(scale))
##                for row in sorted(sortedTheDates, key=lambda student: student[0]):
##                    if row in deltaXDict:
####                        print('deltaXDict[row] ' + str (deltaXDict[row]))
####                        print('deltaXDict[row][6] ' + str(deltaXDict[row][6] ))
##                        deltaXDScaled.append(deltaXDict[row][6] * scale) #/ deltaXDFirst * sortedCalcVIXList[0])
##                        deltaXDScaled_No.append(deltaXDict[row][6])
##                        strikeXD.append(deltaXDict[row][1])
####                print(str(len(sortedCalcVIXList)))
####                print(str(len(deltaXDScaled)))
####                print("Print strikeXD")
####                for row in strikeXD:
####                    print(row)
####                sys.exit(0)
##                        
##                ## Daily PnL
##                strikeChoice = 1 # the index number of the strike we choose (0 is the first). We would wait 2 days to let it settle before trading it, so use 1.
##                numOptionContracts = -1 # -1 is short 1
##                optionPointValue = 100
##                optionPnL = []
##                optionPnLCumSum = []
##                vixFuturePnL = []
##                vixFuturePnLCumSum = []
##                totalPnL = []
##                totalPnLCumSum = []
##                strikeUsedPnL = []
##                optionPositionList = []
##                vixOpn = []
##                vixHigh = []
##                vixLow = []
##                vixClos = []
##                optionAskTheo = []
##                print(str(len(strikeXD)))
##
##                ## loop through everydate we have data for the relevant option expiry
##                for row in sortedTheDates:
##                    todaysDate = row[0]
##                    ## 
##               
##                for i in range(strikeChoice):
##                    optionPnL.append(0.0)
##                    optionPnLCumSum.append(0.0)
##                    vixFuturePnL.append(0)
##                    vixFuturePnLCumSum.append(0)
##                    totalPnL.append(0)
##                    totalPnLCumSum.append(0)
##                    strikeUsedPnL.append(0)
##                    optionPositionList.append(0)
##                    vixOpn.append(0)
##                    vixHigh.append(0)
##                    vixLow.append(0)
##                    vixClos.append(0)
##                    optionAskTheo.append(0)
##                print("strikeChoice")
##                print(str(strikeChoice))
##                print(str(len(strikeXD)-1))
##                while strikeChoice < len(strikeXD)-1:
##                    optionPnL, optionPnLCumSum, vixFuturePnL, vixFuturePnLCumSum, totalPnL, totalPnLCumSum, strikeUsedPnL, optionPositionList, vixOpn, vixHigh, vixLow, vixClos, optionAskTheo  = getDailyPnL(sortedTheDates[strikeChoice-1:], sortedVIXFutureListDict, futureName, deltaTarget, optionExpiryString, optionType, strikeXD, strikeChoice, numOptionContracts, optionPointValue, optionPnL, optionPnLCumSum, vixFuturePnL, vixFuturePnLCumSum, totalPnL, totalPnLCumSum, strikeUsedPnL, optionPositionList, vixOpn, vixHigh, vixLow, vixClos, sortedCalcVIXList, optionAskTheo)
##                    print('Looped')
##                    numOptionContracts = optionPositionList[-1]
##                    strikeChoice = strikeChoice + 1
##                    print(str(strikeChoice))
##                    print(str(numOptionContracts))
####                print('optionPositionList')
####                for row in optionPositionList:
####                    print(row)
####                for row in strikeUsedPnL:
####                    print(row)
##                ##sys.exit(0)
##                fig = plt.figure()
##                ax = fig.add_subplot(111)
##                xAxis = range(len(optionPnLCumSum))
##                ax.plot(xAxis, vixFuturePnLCumSum, 'r-', xAxis, optionPnLCumSum, 'g-', xAxis, totalPnLCumSum, 'k-', xAxis, strikeUsedPnL[0:len(optionPnLCumSum)])
##                ax.legend(['Vix Future', 'Option:' + str(numOptionContracts), 'Total', 'Strike'], loc='best')
##                plt.title(futureName+ " last strike:" + str(strikeUsedPnL[-1]))
##                ax = plt.gca()
##                ax.grid(True)
##                plt.show()
##
##                
##                if printToFile:
##                    fig = plt.figure()
##                    ax = fig.add_subplot(111) 
##                    xAxis = range(len(sortedCalcVIXList))
##    ##                print('xAxis')
##    ##                print(str(len(xAxis)))
##                    ax.plot(xAxis, sortedCalcVIXList, 'r-', xAxis, sortedVIXFutureList, 'g-', xAxis, deltaXDScaled, 'k-')
##                    axes = plt.gca()
##                    axes.set_ylim([0,min(300, max(sortedCalcVIXList)+20, max(deltaXDScaled)+20)])
##                    ax2 = ax.twinx()
##                    ax2.plot(xAxis, sortedUnderlyingList, 'b--')#, strikeXD, 'r--')
##                    ax.legend(['Calculated VIX', 'VIX Future', 'Delta=' + str(deltaTarget) + optionType + ' ' + str(round(scale, 2))], loc='best')
##                    #ax2.legend(['Underlying', 'Strike'], loc=3)
##                    plt.title(futureName)
## 
##                #plt.show()
##                if printToFile:
##                    if fig is not None:
##                        #print(fig)
##                        pp.savefig(fig)
##                        plt.close()
##                    else:
##                        print('fig was none for ' + futureName)
##                        #print(fig)
##            except Exception as inst:
##                print("caught error ...")
##                print(type(inst))    # the exception instance
##                print(inst.args)     # arguments stored in .args
##                print(inst)
##                x, y = inst.args     # unpack args
##                print('x =', x)
##                print('y =', y)
##                if fig is not None and printToFile:
##                    print(fig)
##                    pp.savefig(fig)
##                    plt.close()
##                 # pp.close()
##            # output to  textfile
##            book = xlwt.Workbook()
##            sheet1 = book.add_sheet(futureName)
##            listOfOutputsNames = ['Date', 'CalcVix', 'strikeUsedPnL', 'optionPositionList', 'optionAskTheo', 'VixFuture', 'vixOpn', 'vixHigh', 'vixLow', 'vixClos', 'vixFuturePnL', 'vixFuturePnLCumSum', 'optionPnL', 'optionPnLCumSum', 'totalPnL', 'totalPnLCumSum']
##            listOfOutputs = [sortedTheDates, sortedCalcVIXList, strikeUsedPnL, optionPositionList, optionAskTheo, sortedVIXFutureList, vixOpn, vixHigh, vixLow, vixClos, vixFuturePnL, vixFuturePnLCumSum, optionPnL, optionPnLCumSum, totalPnL, totalPnLCumSum]
####            print(listOfOutputs)
####            print(listOfOutputs[1])
####            sys.exit(0)
##            for outer in range(0, len(listOfOutputsNames)):
##                sheet1.write(0, outer, listOfOutputsNames[outer])
##                for i,e in enumerate(listOfOutputs[outer]):
##                    sheet1.write(i+1,outer,e)
####            sheet1.write(0, 0, 'Date')
####            for i,e in enumerate(sortedTheDates):
####                sheet1.write(i+1,0,e)
####            sheet1.write(0, 1, 'CalcVix')
####            for i,e in enumerate(sortedCalcVIXList):
####                sheet1.write(i+1,1,e)
####            sheet1.write(0, 2, 'VixFuture')
####            for i,e in enumerate(sortedVIXFutureList):
####                sheet1.write(i+1,2,e)
####            sheet1.write(0, 11, 'spotVixHigh')
####            for i,e in enumerate(spotVix):
####                sheet1.write(i+1,11,e)
####            sheet1.write(0, 3, 'UnderlyingIndex')
####            for i,e in enumerate(sortedUnderlyingList):
####                sheet1.write(i+1,3,e)
####            sheet1.write(0, 4, 'ScaledTheo')
####            for i,e in enumerate(deltaXDScaled):
####                sheet1.write(i+1,4,e)
####            sheet1.write(0, 5, 'UnScaledTheo')
####            for i,e in enumerate(deltaXDScaled_No):
####                sheet1.write(i+1,5,e)
####            sheet1.write(0, 6, 'vixFuturePnL')
####            for i,e in enumerate(vixFuturePnL):
####                sheet1.write(i+1,6,e)
####            sheet1.write(0, 7, 'vixFuturePnLCumSum')
####            for i,e in enumerate(vixFuturePnLCumSum):
####                sheet1.write(i+1,7,e)
####            sheet1.write(0, 8, 'optionPnL')
####            for i,e in enumerate(optionPnL):
####                sheet1.write(i+1,7,e)
####            sheet1.write(0, 9, 'optionPnLCumSum')
####            for i,e in enumerate(optionPnLCumSum):
####                sheet1.write(i+1,8,e)
####            sheet1.write(0, 10, 'totalPnL')
####            for i,e in enumerate(totalPnL):
####                sheet1.write(i+1,7,e)
####            sheet1.write(0, 11, 'totalPnLCumSum')
####            for i,e in enumerate(totalPnLCumSum):
####                sheet1.write(i+1,8,e)
####            sheet1.write(0, 12, 'strikeUsedPnL')
####            for i,e in enumerate(strikeUsedPnL):
####                sheet1.write(i+1,9,e)
####            sheet1.write(0, 13, 'optionPositionList')
####            for i,e in enumerate(optionPositionList):
####                sheet1.write(i+1,10,e)
##
##            book.save("singleExpiryAnalytics_" + now.strftime("%Y-%m-%d") + ".xls")
####            for trow in sorted(theDates, key=lambda x: datetime.datetime.strptime(x, "%Y-%m-%d")):
####                print(trow)
##            sys.exit(0)
##    now2 = datetime.datetime.now()       
##    print('Done : ' + str(deltaTarget) + ' :' + str(now.strftime("%Y-%m-%d %H:%M")))
##    pp.close()
