import MySQLdb as mdb
import sys
from decimal import *
import matplotlib.pyplot as plt

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")
def getDailyPnL(sortedVIXFutureList, futureName, deltaTarget, optionExpiryString, optionType, strike, strikeChoice, numOptionContracts, optionPointValue):
    
    sqlQuery = ('select oe.quote_date, oe.Expiration, st.strike, st.option_type, og.delta_1545, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545, og.vega_1545, '
        'case when st.option_type = "c" then abs(%s - delta_1545) else abs(%s - (1-abs(delta_1545))) end as "delta_gap" from optiongreeks og ' 
        'join optionexpiry oe on oe.ID = og.optionexpiryID '
        'join strike st on st.ID = og.strikeID '
        'where oe.ID in '
        '( '
        'select ID from optionexpiry where root in ("SPX") and expiration = '"'%s'"' '
        ') '
        'and st.option_type = '"'%s'"' '
        'and st.strike = %s '
        'order by oe.quote_date, oe.Expiration, st.strike;' % (deltaTarget, deltaTarget, optionExpiryString, optionType, strike))

    print(sqlQuery)

    cur = con.cursor()
    cur.execute(sqlQuery)
    strikeDataRaw = cur.fetchall()
    cur.close()

    optionPnL = []
    optionPnLCumSum = []
    vixFuturePnL = []
    vixFuturePnLCumSum = []
    totalPnL = []
    totalPnLCumSum = []
    counter = 0
    for row in strikeDataRaw:
        if counter < strikeChoice:
            optionPnL.append(0.0)
            optionPnLCumSum.append(0.0)
            vixFuturePnL.append(0)
            vixFuturePnLCumSum.append(0)
            totalPnL.append(0)
            totalPnLCumSum.append(0)
        elif counter == strikeChoice:
            val = (row[6] - row[5]) * numOptionContracts * optionPointValue # pay spread (bid less ask)
            optionPnL.append(val) 
            optionPnLCumSum.append(val + optionPnLCumSum[-1])
            futVal = (Decimal(sortedVIXFutureList[counter]) - Decimal(sortedVIXFutureList[counter - 1])) * Decimal(1) * Decimal(1000)
            vixFuturePnL.append(futVal)
            vixFuturePnLCumSum.append(futVal + vixFuturePnLCumSum[-1])
            totalPnL.append(Decimal(optionPnL[-1]) + Decimal(vixFuturePnL[-1]))
            totalPnLCumSum.append(Decimal(optionPnLCumSum[-1]) + Decimal(vixFuturePnLCumSum[-1]))
        else:
            val = (row[6] - previousRow[6]) * numOptionContracts * optionPointValue
            optionPnL.append(val) # hit ask to buy contract back
            optionPnLCumSum.append(val + optionPnLCumSum[-1])
            if Decimal(sortedVIXFutureList[counter]) > 1 and Decimal(sortedVIXFutureList[counter - 1]) > 1: # check VixFuture is less than 1 vol (may have expired or not started trading yet)
                futVal = (Decimal(sortedVIXFutureList[counter]) - Decimal(sortedVIXFutureList[counter - 1])) * Decimal(1) * Decimal(1000)
                vixFuturePnL.append(futVal)
                vixFuturePnLCumSum.append(futVal + vixFuturePnLCumSum[-1])
            else:
                vixFuturePnL.append(0)
                vixFuturePnLCumSum.append(vixFuturePnLCumSum[-1])
            totalPnL.append(Decimal(optionPnL[-1]) + Decimal(vixFuturePnL[-1]))
            totalPnLCumSum.append(Decimal(optionPnLCumSum[-1]) + Decimal(vixFuturePnLCumSum[-1]))
        counter = counter + 1
        previousRow = row
    fig = plt.figure()
    ax = fig.add_subplot(111)
    xAxis = range(len(optionPnLCumSum))
    print(str(len(vixFuturePnLCumSum)))
    print(str(len(optionPnLCumSum)))
    print(str(len(totalPnLCumSum)))
    ax.plot(xAxis, vixFuturePnLCumSum, 'r-', xAxis, optionPnLCumSum, 'g-', xAxis, totalPnLCumSum, 'k-')
    ax.legend(['Vix Future', 'Option:' + str(numOptionContracts), 'Total'], loc='best')
    plt.title(futureName)
    ax = plt.gca()
    ax.grid(True)
    plt.show()
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
    return optionPnL, optionPnLCumSum
