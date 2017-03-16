import MySQLdb as mdb
import sys
from decimal import *
import matplotlib.pyplot as plt
import datetime

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")

def queryStrikeThroughtime(deltaTarget, optionExpiryString, optionType, strike):
       return ('select oe.quote_date, oe.Expiration, st.strike, st.option_type, og.delta_1545, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545, og.vega_1545, '
        'case when st.option_type = "c" then abs(%s - delta_1545) else abs(%s - (1-abs(delta_1545))) end as "delta_gap", vi.High from optiongreeks og ' 
        'join optionexpiry oe on oe.ID = og.optionexpiryID '
        'join strike st on st.ID = og.strikeID '
        'join VIX vi on vi.Tradedate = left(oe.quote_date, 10) '
        'where oe.ID in '
        '( '
        'select ID from optionexpiry where root in ("SPX") and expiration = '"'%s'"' '
        ') '
        'and st.option_type = '"'%s'"' '
        'and st.strike = %s '
        'order by oe.quote_date, oe.Expiration, st.strike;' % (deltaTarget, deltaTarget, optionExpiryString, optionType, strike))


def getDailyPnL(sortedTheDates, sortedVIXFutureListDict, futureName, deltaTarget, optionExpiryString, optionType, strikeList, strikeChoice, numOptionContracts, optionPointValue, optionPnL, optionPnLCumSum, vixFuturePnL, vixFuturePnLCumSum, totalPnL, totalPnLCumSum, strikeUsedPnL, optionPositionList, spotVix):

    sqlQuery = queryStrikeThroughtime(deltaTarget, optionExpiryString, optionType, strikeList[strikeChoice])
    cur = con.cursor()
    cur.execute(sqlQuery)
    strikeDataRaw = cur.fetchall()
    cur.close()
    print(sqlQuery)
    # create a dictionary to put data from db in
    dbDateDict = {}
    for row in strikeDataRaw:
       valueList = list()
       for f in range(0, 12):
           valueList.append(row[f])
           dbDateDict[datetime.datetime.strftime(row[0], "%Y-%m-%d")] = valueList
    
    counter = strikeChoice -1 # we do this because we bring in a day earlier than we need, to enable VixFuture PnL
    numOptionContractsOriginal = numOptionContracts
    #strike = strikeList[strikeChoice]
    for dateRow in sortedTheDates:
        dateRowKey = dateRow
        if dateRowKey in dbDateDict:
               row = dbDateDict[dateRowKey]
               #print(row)
               if counter < strikeChoice:
                     skipIt = 1.0
       ##            optionPnL.append(0.0)
       ##            optionPnLCumSum.append(0.0)
       ##            vixFuturePnL.append(0)
       ##            vixFuturePnLCumSum.append(0)
       ##            totalPnL.append(0)
       ##            totalPnLCumSum.append(0)
               elif counter == strikeChoice:
                   val = (row[6] - row[5]) * numOptionContracts * optionPointValue # pay spread (bid less ask)
                   optionPnL.append(val) 
                   optionPnLCumSum.append(val + optionPnLCumSum[-1])
                   futVal = (Decimal(sortedVIXFutureListDict[dateRowKey]) - Decimal(sortedVIXFutureListDict[previousDateKey])) * Decimal(1) * Decimal(1000)
                   vixFuturePnL.append(futVal)
                   vixFuturePnLCumSum.append(futVal + vixFuturePnLCumSum[-1])
                   totalPnL.append(Decimal(optionPnL[-1]) + Decimal(vixFuturePnL[-1]))
                   totalPnLCumSum.append(Decimal(optionPnLCumSum[-1]) + Decimal(vixFuturePnLCumSum[-1]))
                   if numOptionContracts == 0:
                      strikeUsedPnL.append(0)
                   else:
                      strikeUsedPnL.append(row[2])
                   spotVix.append(row[11])
                   optionPositionList.append(numOptionContracts)
               else:               
                   val = (row[6] - previousRow[6]) * numOptionContracts * optionPointValue
##                   print('val ' + str(val))
##                   print('row ' + str(row))
##                   print('previousRow ' + str(previousRow))
##                   sys.exit(0)
                   optionPnL.append(val) # hit ask to buy contract back
                   optionPnLCumSum.append(val + optionPnLCumSum[-1])
                   if Decimal(sortedVIXFutureListDict[dateRowKey]) > 1 and Decimal(sortedVIXFutureListDict[previousDateKey]) > 1: # check VixFuture is less than 1 vol (may have expired or not started trading yet)
                       futVal = (Decimal(sortedVIXFutureListDict[dateRowKey]) - Decimal(sortedVIXFutureListDict[previousDateKey])) * Decimal(1) * Decimal(1000)
                       vixFuturePnL.append(futVal)
                       vixFuturePnLCumSum.append(futVal + vixFuturePnLCumSum[-1])
                   else:
                       vixFuturePnL.append(0)
                       vixFuturePnLCumSum.append(vixFuturePnLCumSum[-1])
                   totalPnL.append(Decimal(optionPnL[-1]) + Decimal(vixFuturePnL[-1]))
                   totalPnLCumSum.append(Decimal(optionPnLCumSum[-1]) + Decimal(vixFuturePnLCumSum[-1]))
                   if numOptionContracts == 0:
                      strikeUsedPnL.append(0)
                   else:
                      strikeUsedPnL.append(row[2])
                   spotVix.append(row[11])
                   optionPositionList.append(numOptionContracts)
                   if sortedVIXFutureListDict[dateRowKey] < row[11]:
                       numOptionContracts = 0 # close the position when VixFuture level falls below spot VIX
                   elif numOptionContracts == 0 and  (sortedVIXFutureListDict[dateRowKey] - row[11]) > 3: # we put the position back on
                       return counter+1, optionPnL, optionPnLCumSum, vixFuturePnL, vixFuturePnLCumSum, totalPnL, totalPnLCumSum, strikeUsedPnL, optionPositionList, spotVix
                       
               counter = counter + 1
               previousRow = row
               previousDateKey = dateRowKey

##    for row in optionPnL:
##        print(row)
##    for row in optionPnLCumSum:
##        print(row)
##    print('sortedVIXFutureList')
##    for row in sortedVIXFutureList:
##        print(row)
##    print('vixFuturePnL')
##    for row in vixFuturePnL:
##        print(row)
##    print('vixFuturePnLCumSum')
##    for row in vixFuturePnLCumSum:
##        print(row)        
    return counter, optionPnL, optionPnLCumSum, vixFuturePnL, vixFuturePnLCumSum, totalPnL, totalPnLCumSum, strikeUsedPnL, optionPositionList, spotVix
