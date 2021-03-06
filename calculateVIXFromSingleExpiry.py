#import MySQLdb as mdb
import pymysql as mdb
from operator import itemgetter
#import sys
import datetime
import math
import bisect
#import xlrd
#from ImportFromExcel import importExcelVol
from Replicate_VIX_Calculation import outputDictionary, f, isolateStrikes, calculateExpiryVarianceContribution, calculateStrikeContributionToVIX, calculateExpiryVariance
#import sys

def calculateVIXFromSingleExpiry(quote_date, optionExpiration_date, r, printResults=False, use30DaysToExpiry=True, useOwnData=None):
    if printResults:
        print('calculateVIXFromSingleExpiry: quote_date: ' + str(quote_date))
    # connect to db
    con = mdb.connect(host="localhost",user="root",
                      passwd="password",db="Vol", port = 3307)
    if useOwnData is None:
        # bring back strike level information for expiration on quote_date
        sqlQuery = ('select oe.Expiration, st.strike, st.option_type, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545 from optiongreeks og '
        'join optionexpiry oe on oe.ID = og.optionexpiryID '
        'join strike st on st.ID = og.strikeID '
        'where og.optionexpiryID = '
        '('
        'select ID from optionexpiry where substring(quote_date, 1, 10) = '"'%s'"' and root in ("SPX") and expiration = '"'%s'"''
        ')'
        'order by oe.Expiration, st.strike;' % (quote_date, optionExpiration_date))
        cur = con.cursor()
        cur.execute(sqlQuery)
        sqlResults = cur.fetchall()
        cur.close()
    else:
        sqlResults = useOwnData
    if printResults:
        print(sqlQuery)
    # create vectors
    strike = list()
    option_type = list()
    bid = list()
    ask = list()
    avgBidAsk = list()
    impvol = list()
    for item in sqlResults:
        strike.append(item[1])
        option_type.append(item[2])
        bid.append(item[3])
        ask.append(item[4])
        avgBidAsk.append(item[5])
        impvol.append(item[6])
    # sql query has sorted by strike already, so don't need to do that
    # now use a dictionary to organise the data
    expiryDict = {}
    expiryDict = outputDictionary(expiryDict, strike, option_type, bid, avgBidAsk, impvol)
    # now move the data from dictionary to a list so is more usable
    expiryList = []
    expiryListWithoutZeroCallAndPutBid = []
    for key, value in expiryDict.items():
        aList = list()
        aList = [float(key), value[0], value[1], value[2], value[3], value[4], value[5], value[6]]
        expiryList.append(aList)
        # expiryList to find expiryForwardIndex
        if value[1] == 0.0 and value[4] == 0.0:
            ## skip this row
            skipThisRow = 1
        else:
            expiryListWithoutZeroCallAndPutBid.append(aList)
        ## debug purposes
##        if key == '2435.0':
##            print('Found Key!')
##            for x in range(0, 6):
##                print(str(value[x]))
##            sys.exit(0)
    expiryListSorted = sorted(expiryList, key=lambda student: student[f("strike")], reverse=False)
    expiryListWithoutZeroCallAndPutBidSorted = sorted(expiryListWithoutZeroCallAndPutBid, key=lambda student: student[f("strike")], reverse=False)
    if printResults:
        print('expiryList')
        print(expiryList)
        print('expiryListSorted')
        print(expiryListSorted)
        print('expiryListWithoutZeroCallAndPutBidSorted')
        print(expiryListWithoutZeroCallAndPutBidSorted)
    # expiry time in minutes
    if use30DaysToExpiry:
        expiryTTEminutes = 30 * 24 * 60
    else: # use actual number of days to option maturity
        #print('day delta test')
        #print(str(max((datetime.datetime.strptime(optionExpiration_date, "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(quote_date, "%Y-%m-%d")).days, 1)))
        expiryTTEminutes = max((datetime.datetime.strptime(optionExpiration_date, "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(quote_date, "%Y-%m-%d")).days, 1) * 24 * 60
    expiryTTE365Dminutes = 365 * 24 * 60
    expiryTTEyears = expiryTTEminutes / expiryTTE365Dminutes
    ## Determine the forward SPX level where min(abs(c_avgBidAsk - p_avgBidAsk)), but don't include strikes where both call and put bids are zero
    if len(expiryListWithoutZeroCallAndPutBidSorted) < 1:
        print('No data - VIX is zero')
        return 0.0
    else:
        expiryForwardRow = min(expiryListWithoutZeroCallAndPutBidSorted,key=itemgetter(f("callLessPutTheo")))
    expiryForward = expiryForwardRow[f("strike")]
    expiryForwardIndex = expiryForward + math.exp(expiryTTEyears * r) * (expiryForwardRow[f("c_avgBidAsk")] - expiryForwardRow[f("p_avgBidAsk")])
    ## determine the strike immediately below the forwardIndex
    expiryForwardIndexIndex = bisect.bisect([row[f("strike")] for row in expiryListSorted], expiryForwardIndex)
    expiryK0Strike = expiryListSorted[expiryForwardIndexIndex-1][f("strike")]
    if printResults:
        print('expiryK0Strike: ' + str(expiryK0Strike))
        print('expiryForwardIndex: ' + str(expiryForwardIndex))
    ## isolate puts and calls
    # Puts
    expiryListSortedReverse = sorted(expiryList, key=lambda student: student[f("strike")], reverse=True)
    expiryPutList = [t for t in expiryListSortedReverse if t[f("strike")] < expiryK0Strike] # get all strikes below K0, starting with strike immediately below K0 and decreasing
    if printResults:
        print('expiryPutList')
        print(expiryPutList)
    countZeroBidPrices = 0
    expiryPutListZeroBidChecked = list()
    expiryPutListZeroBidChecked = isolateStrikes(expiryPutList, "p_bid", countZeroBidPrices)
    if printResults:
        print('expiryPutListZeroBidChecked')
        print(expiryPutListZeroBidChecked)
    # Calls
    expiryCallList = [t for t in expiryListSorted if t[f("strike")] > expiryK0Strike] # get all strikes above K0, starting with strike immediately above K0 and increasing
    if printResults:
        print('expiryCallList')
        print(expiryCallList)
    countZeroBidPrices = 0
    expiryCallListZeroBidChecked = list()
    expiryCallListZeroBidChecked = isolateStrikes(expiryCallList, "c_bid", countZeroBidPrices)
    if printResults:
        print('expiryCallListZeroBidChecked')
        print(expiryCallListZeroBidChecked)
    if len(expiryCallListZeroBidChecked) < 2 or len(expiryPutListZeroBidChecked) < 2:
        print('Not enough data to calculate a VIX, so return zero')
        return 0.0

    # the K0 strike
    expiryK0RowTemp = [t for t in expiryList if t[f("strike")] == expiryK0Strike]
    expiryK0Row = expiryK0RowTemp[0]
    # contribution to Variance
    expiryPutListZeroBidCheckedContribution = calculateExpiryVarianceContribution(expiryPutListZeroBidChecked, r, expiryTTEyears, "p_avgBidAsk", expiryForwardIndex, "p_impVol")
    expiryCallListZeroBidCheckedContribution = calculateExpiryVarianceContribution(expiryCallListZeroBidChecked, r, expiryTTEyears, "c_avgBidAsk", expiryForwardIndex, "c_impVol")
    if printResults:
        print('expiryCallListZeroBidCheckedContribution:')
        print(expiryCallListZeroBidCheckedContribution)
        print('expiryPutListZeroBidCheckedContribution:')
        print(expiryPutListZeroBidCheckedContribution)
    # control for when there are no puts or calls with non-zero bids
    if len(expiryPutListZeroBidCheckedContribution) > 0 and len(expiryCallListZeroBidCheckedContribution) > 0: 
        expiryK0StrikeDelta = (expiryCallListZeroBidCheckedContribution[0][f("strike")] - expiryPutListZeroBidCheckedContribution[0][f("strike")] ) / 2
    elif len(expiryPutListZeroBidCheckedContribution) == 0 and len(expiryCallListZeroBidCheckedContribution) == 0:
        print('return zero; the lists of puts and of calls both have length zero')
        return 0.0
    elif len(expiryPutListZeroBidCheckedContribution) > 0 and len(expiryCallListZeroBidCheckedContribution) == 0:
        expiryK0StrikeDelta = expiryPutListZeroBidCheckedContribution[0][f("strike")]
    else:
        print('expiryCallListZeroBidCheckedContribution')
        print(expiryCallListZeroBidCheckedContribution)
        expiryK0StrikeDelta = expiryCallListZeroBidCheckedContribution[0][f("strike")] 

    expiryK0Contribution = expiryK0StrikeDelta / math.pow(expiryK0Strike, 2) * math.exp(r * expiryTTEyears) * (expiryK0Row[f("c_avgBidAsk")] + expiryK0Row[f("p_avgBidAsk")])/2
    expiryK0Row.append(expiryK0Contribution)
    if printResults:
        print('expiryK0Row')
        print(expiryK0Row)
    expiryK0Row.append(calculateStrikeContributionToVIX(expiryK0Row[f("strike")], expiryK0Row[f("c_impVol")], r, expiryForwardIndex, expiryTTEyears))

    # combine puts, calls and K0 together
    expiryContributionList = list()
    expiryContributionList.extend(expiryPutListZeroBidCheckedContribution)
    expiryContributionList.extend(expiryCallListZeroBidCheckedContribution)
    expiryContributionList.append(expiryK0Row)
    expiryVariance, expiryStrikeContribution = calculateExpiryVariance(expiryContributionList, expiryTTEyears, expiryK0Row[f("strike")], expiryForwardIndex)
    # calculate VIX
    scaleTo365D = expiryTTE365Dminutes / expiryTTEminutes
    VixCalc = expiryTTEyears * expiryVariance
    if VixCalc < 0:
        print('VixCalc is negative, return 0. Quote_date = ' + str(quote_date) + ' It will be because of the large difference between the expiryForwardIndex and the expiryK0Strike')
        return 0.0
    VIX = 100 * math.pow(VixCalc * scaleTo365D, 0.5)
    return VIX
    
###### Up to line 345 in Replicate_VIX_Calculation (isolateStrikes). Need to check that K0 is correct, and so are call and put lists
## Check after making changes to Replicate_VIX_Calculation that running VIV_By_Date gives VIX: 15.753136281361032
# Test
##optionExpiration_date = '2017-01-20 08:30:00'
##futuresExpiryDateTemp = datetime.datetime.strptime(optionExpiration_date[0:10], "%Y-%m-%d")
##futuresExpiryDate = futuresExpiryDateTemp.strftime("%Y-%m-%d")
##print(futuresExpiryDate)
##con = mdb.connect(host="localhost",user="root",
##                  passwd="password",db="Vol")
##sqlQuery = ('Select TradeDate, Contract, Clos from VIXFutures '
##'where Contract = '
##'('
##	'select Contract from VIXFuturesExpiry '
##	'where Expirydate = '"'%s'"' '
##');' % futuresExpiryDate)
##print(sqlQuery)
##cur = con.cursor()
##cur.execute(sqlQuery)
##vixFuturesDataRaw = cur.fetchall()
##cur.close()
##
##for row in vixFuturesDataRaw:
##    print(row)
##sys.exit(0)
####quote_date = '2016-09-21'
##
##sqlQuery = ('select quote_date from OptionExpiry '
##    'where expiration = '"'%s'"' ' 
##    'and rootOriginal = '"'SPX'"' '
##    'group by quote_date '
##    'order by quote_date;' % optionExpiration_date)
##print(sqlQuery)
##cur = con.cursor()
##cur.execute(sqlQuery)
##quote_dates = cur.fetchall()
##cur.close()
##
##r = 0.01
##for dt in quote_dates:
##    #print(str(dt[0].strftime("%Y-%m-%d")))
##    VIX = calculateVIXFromSingleExpiry(str(dt[0].strftime("%Y-%m-%d")), optionExpiration_date, r, False)
##    print(str(dt[0].strftime("%Y-%m-%d")) + ":" + str(VIX))

