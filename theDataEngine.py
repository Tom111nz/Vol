#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  2 15:12:22 2018

@author: tomobrien
"""

### the engine to collect the data we require
import datetime
from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
from InterpolateUSYield import interpolateUSYield
from GetDeltaThroughTime import getDeltaThroughTime
import pymysql as mdb
import math
import traceback
import pdb

def bugHunter(err):
    print(err)
    template = "An exception of type {0} occurred. Arguments:\n{1!r}"
    message = template.format(type(err).__name__, err.args)
    print(message)
    print(traceback.format_exc())
    pdb.post_mortem()

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol", port = 3307)

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


def theDataEngine(deltaTargetList, VIXFutureOptionExpiryLists):
    colHeaders = ['calculatedVIX', 'underling bid', 'VIX Future settle', 'Vix Opn', 'Vix High', 'Vix Low', 'Vix Clos',
            'strike', 'option_type', 'delta', 'bid', 'ask', 'mid', 'imp_vol', 'vega', 'deltalessX', 'sqrtTTE']
    dKey = {}
    for j in range(0, len(colHeaders)): # create numbering key for use below
        dKey[colHeaders[j]] = j    
    deltaDict = {}
    for deltaTarget in deltaTargetList:
        #pp = PdfPages('Analytics_ActualYield_' + str(now.strftime("%Y-%m-%d")) + '_' + str(deltaTarget) + '.pdf') 
    # Loop through VIX Futures
        futuresDict = {}
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
                        sqrtTTE = math.sqrt(max((futureExpiryDatetime - quoteDate).days, 1) / 365.0)
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
                        iList.append(sqrtTTE)
                        dailyValuesDict[quoteDateKey] = iList
                    else:
                        print('skipping same date :' + optionExpiryString + " : " + str(datetime.datetime.strftime(row[0], "%Y-%m-%d")))
                except Exception as err:
                    bugHunter(err)
#                    print('error here')
#                    print(type(inst))    # the exception instance
#                    print(inst.args)     # arguments stored in .args
#                    print(inst)
#                    x, y = inst.args     # unpack args
#                    print('x =', x)
#                    print('y =', y)
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

            #sortedKeys = sorted(dailyValuesDict.keys())
            futuresDict[futureName] = dailyValuesDict
        deltaDict[deltaTarget] = futuresDict
    return dKey, deltaDict