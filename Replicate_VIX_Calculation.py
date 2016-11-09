## Replicate the VIX calculation


# choose day from this article
# http://www.cboeoptionshub.com/2014/10/03/vix-spot-index-include-sp-500-weekly-options-beginning-oct-6th-part-1/

import MySQLdb as mdb
from operator import itemgetter
import sys
import datetime
import math
import bisect
import xlrd
from ImportFromExcel import importExcelVol 

## Download Github and github desktop ?
## Can the interest rates be scrapped programmatically ?
## Look at the expiries that make up the VIX through time. How often do the expiry changes ? Once the weeklies are listed, do the expiries stay til expiration ?
## Does every VIX future expire into a single SPX or SPXW option series ?
## Need to bring in all expiries for given day into python from db, determine which expiries we use (the closest two either side of 30/365 (?), and then go back to db and request the strike, put/call bid/ask details
## Also consider calculating VIN and VIF

def calculateVIX(quote_date, printResults=False):
    #quote_date = "2014-10-06"
    if printResults:
        print("Quote_date: " + quote_date)
    quote_dateTime = quote_date + " 15:45:00" # This is the time of the data received from CBOE
    quote_date_nextDay = datetime.datetime.strptime(quote_date + " 00:00:00", "%Y-%m-%d %H:%M:%S") + datetime.timedelta(days=1)
    expiryTTE30Dminutes = 30 * 24 * 60
    expiryTTE365Dminutes = 365 * 24 * 60

    con = mdb.connect(host="localhost",user="root",
                      passwd="password",db="Vol")
    cur = con.cursor()

    # Get all the expiries for the quote_date
    sqlQueryQuoteDateExpiries = ('select * from optionexpiry '
    'where substring(quote_date, 1, 10) = '"'%s'"' '
    'and rootOriginal in ("SPX", "SPXW") '
    'order by expiration;' % quote_date)
    cur.execute(sqlQueryQuoteDateExpiries)
    sqlQueryQuoteDateExpiriesResults = cur.fetchall()
    cur.close()

    # identify the SPX results and subtract a day (the expiry day in db is a Saturday, but we use the Friday in VIX calculations)
    sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry = list()
    for row in sqlQueryQuoteDateExpiriesResults:
        newRow = list(row)
        if row[2] == 'SPX':
            newRow.append(datetime.datetime.strptime(str(row[3]), "%Y-%m-%d %H:%M:%S") - datetime.timedelta(days=1))
            sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry.append(newRow)
        else:
            newRow.append(datetime.datetime.strptime(str(row[3]), "%Y-%m-%d %H:%M:%S"))
            sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry.append(newRow)
            
    # calculate time to expiry in miutes
    for row in sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry:
        timeToExpiry = datetime.datetime.strptime(str(row[6]), "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(quote_dateTime, "%Y-%m-%d %H:%M:%S")
        row.append(timeToExpiry.total_seconds() / 60)

    ##find expiries either side of 30 days
    indexOfFarExpiry = bisect.bisect([row[7] for row in sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry], expiryTTE30Dminutes)
    indexOfNearExpiry = indexOfFarExpiry - 1

    nearExpiryDate = sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry[indexOfNearExpiry][6]
    farExpiryDate = sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry[indexOfFarExpiry][6]
    strNearExpiryDate = str(nearExpiryDate)
    strFarExpiryDate = str(farExpiryDate)

    nearExpiryDateDb = sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry[indexOfNearExpiry][3]
    farExpiryDateDb = sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry[indexOfFarExpiry][3]

    nearExpiryContractType = sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry[indexOfNearExpiry][2]
    farExpiryContractType = sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry[indexOfFarExpiry][2]

    if printResults:
        print("NearExpiry: " + strNearExpiryDate)
        print("FarExpiry: " + strFarExpiryDate)
        print("nearExpiryDateDb: " + str(nearExpiryDateDb))
        print("farExpiryDateDb: " + str(farExpiryDateDb))
        print("nearExpiryContractType: " + str(nearExpiryContractType))
        print("farExpiryContractType: " + str(farExpiryContractType))
    
    ## Retrieve the strike level data for these dates
    sqlQuery = ('select oe.Expiration, st.strike, st.option_type, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545 from optiongreeks og '
    'join optionexpiry oe on oe.ID = og.optionexpiryID '
    'join strike st on st.ID = og.strikeID '
    'where og.optionexpiryID in '
    '('
    'select ID from optionexpiry where substring(quote_date, 1, 10) = '"'%s'"' and rootOriginal in ("SPX", "SPXW") and ID in ("%s", "%s")'
    ')'
    'order by oe.Expiration, st.strike;' % (quote_date, sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry[indexOfNearExpiry][0], sqlQueryQuoteDateExpiriesResultsFixedSPXExpiry[indexOfFarExpiry][0]))
    cur = con.cursor()
    cur.execute(sqlQuery)
    sqlResults = cur.fetchall()
    cur.close()

    if printResults:
        print(sqlQuery)
    
    optionExpiryID = list()
    strike = list()
    option_type = list()
    bid = list()
    ask = list()
    avgBidAsk = list()
    impvol = list()
    for item in sqlResults:
        if datetime.datetime.strptime(str(item[0]), "%Y-%m-%d %H:%M:%S") == datetime.datetime.strptime(str(nearExpiryDateDb), "%Y-%m-%d %H:%M:%S"):
            optionExpiryID.append(0)
        else:
            optionExpiryID.append(1)
        strike.append(item[1])
        option_type.append(item[2])
        bid.append(item[3])
        ask.append(item[4])
        avgBidAsk.append(item[5])
        impvol.append(item[6])

    nearExpiryPos = [i for i,x in enumerate(optionExpiryID) if x == 0]
    farExpiryPos = [i for i,x in enumerate(optionExpiryID) if x == 1]
    nearExpiryStrike = [strike[i] for i in nearExpiryPos]
    farExpiryStrike = [strike[i] for i in farExpiryPos]
    nearExpiryOption_type = [option_type[i] for i in nearExpiryPos]
    farExpiryOption_type = [option_type[i] for i in farExpiryPos]
    nearExpiryBid = [bid[i] for i in nearExpiryPos]
    farExpiryBid = [bid[i] for i in farExpiryPos]
    nearExpiryAsk = [ask[i] for i in nearExpiryPos]
    farExpiryAsk = [ask[i] for i in farExpiryPos]
    nearExpiryAvgBidAsk = [avgBidAsk[i] for i in nearExpiryPos]
    farExpiryAvgBidAsk = [avgBidAsk[i] for i in farExpiryPos]
    nearExpiryImpVol = [impvol[i] for i in nearExpiryPos]
    farExpiryImpVol = [impvol[i] for i in farExpiryPos]

    if printResults:
        print("NearExpiryCount: " + str(len(nearExpiryPos)))
    
    # make sure both expiries are sorted by strike
    nearExpiryZipped = zip(nearExpiryStrike, nearExpiryOption_type, nearExpiryBid, nearExpiryAvgBidAsk, nearExpiryImpVol)
    nearExpiryZippedSorted = sorted(nearExpiryZipped, key=lambda student: student[0])

    farExpiryZipped = zip(farExpiryStrike, farExpiryOption_type, farExpiryBid, farExpiryAvgBidAsk, farExpiryImpVol)
    farExpiryZippedSorted = sorted(farExpiryZipped, key=lambda student: student[0])

    # create list of strike, callAvgBidAsk, putAvgBidAsk, Bid, ImpVol
    def outputDictionary(aDict, strike, option_type, bid, avgBidAsk, impVol):
        for i in range(len(strike)):
             # create the dictionary key if not already created
            if str(strike[i]) not in aDict:
                aDict[str(strike[i])] = [0]*7 # use a string because float is not iterable later on
            # Get the value list from dictionary 
            aValues = aDict.get(str(strike[i]))
            # Populate the list
            if option_type[i] == 'c':
                aValues[0] = bid[i]
                aValues[1] = avgBidAsk[i]
                aValues[2] = impVol[i]
            else:
                aValues[3] = bid[i]
                aValues[4] = avgBidAsk[i]
                aValues[5] = impVol[i]
            # repopulate the dictionary
            aValues[6] = abs(aValues[1] - aValues[4]) # absolute of call - put at strike
            aDict[str(strike[i])] = aValues
        return aDict # key: strike, value: [c_bid, c_avgBidAsk, c_impVol, p_bid, p_avgBidAsk, p_impVol, c_avgBidAsk - p_avgBidAsk]

    # set up fetching dictionary
    columnLookupDict = {}
    columnLookupDict["strike"] = 0
    columnLookupDict["c_bid"] = 1
    columnLookupDict["c_avgBidAsk"] = 2
    columnLookupDict["c_impVol"] = 3
    columnLookupDict["p_bid"] = 4
    columnLookupDict["p_avgBidAsk"] = 5
    columnLookupDict["p_impVol"] = 6
    columnLookupDict["callLessPutTheo"] = 7
    columnLookupDict["varianceContribution"] = 8
    def f(columnName):
        if columnName in columnLookupDict:
            return columnLookupDict.get(columnName)
        else:
            print(str(columnName) + " not in columnLookupDict. Now we exit.")
            sys.exit(0)
       
    nearExpiryDict = {}
    nearExpiryDict = outputDictionary(nearExpiryDict, nearExpiryStrike, nearExpiryOption_type, nearExpiryBid, nearExpiryAvgBidAsk, nearExpiryImpVol)

    farExpiryDict = {}
    farExpiryDict = outputDictionary(farExpiryDict, farExpiryStrike, farExpiryOption_type, farExpiryBid, farExpiryAvgBidAsk, farExpiryImpVol)

    nearExpiryList = []
    for key, value in nearExpiryDict.items():
        aList = list()
        aList = [float(key), value[0], value[1], value[2], value[3], value[4], value[5], value[6]]
        nearExpiryList.append(aList)

    farExpiryList = []
    for key, value in farExpiryDict.items():
        aList = list()
        aList = [float(key), value[0], value[1], value[2], value[3], value[4], value[5], value[6]]
        farExpiryList.append(aList)

    ############## Import data from excel file
    nearExpiryListSorted = sorted(nearExpiryList, key=lambda student: student[0])
    farExpiryListSorted = sorted(farExpiryList, key=lambda student: student[0])

    ##nearExpiryListSorted, farExpiryListSorted = importExcelVol()

    ##############

    ## Time to Expiry (Need to change SQL query to pick these expiries up, also need to make quote_date in sql query a parameter)
    minutesToMidnightOfCurrentDayTemp = datetime.datetime.strptime(str(quote_date_nextDay), "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(quote_dateTime, "%Y-%m-%d %H:%M:%S")
    minutesToMidnightOfCurrentDay = minutesToMidnightOfCurrentDayTemp.seconds / 60

    minutesFromMidnightToNearExpiryTimeTemp = datetime.datetime.strptime(quote_date + " " + strNearExpiryDate[11:19], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(quote_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    minutesFromMidnightToNearExpiryTime = minutesFromMidnightToNearExpiryTimeTemp.seconds / 60
    if printResults:
        print(strFarExpiryDate[11:19])
        print(strNearExpiryDate[11:19])
    minutesFromMidnightToFarExpiryTimeTemp = datetime.datetime.strptime(quote_date + " " + strFarExpiryDate[11:19], "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(quote_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    minutesFromMidnightToFarExpiryTime = minutesFromMidnightToFarExpiryTimeTemp.seconds / 60

    daysToExpiryNearExpiryTemp = datetime.datetime.strptime(strNearExpiryDate[0:10] + " 00:00:00", "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(quote_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    daysToExpiryNearExpiry = (daysToExpiryNearExpiryTemp.days - 1) * (24*60) 

##    print("quote_date: " + quote_date)
##    print("ExpiryDay: " + strNearExpiryDate[0:10])
##    print(str(daysToExpiryNearExpiryTemp.days))
##    sys.exit(0)
    
    daysToExpiryFarExpiryTemp = datetime.datetime.strptime(strFarExpiryDate[0:10] + " 00:00:00", "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(quote_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    daysToExpiryFarExpiry = (daysToExpiryFarExpiryTemp.days - 1) * (24*60) 

    nearExpiryTTE = (minutesToMidnightOfCurrentDay + minutesFromMidnightToNearExpiryTime + daysToExpiryNearExpiry) / expiryTTE365Dminutes
    farExpiryTTE = (minutesToMidnightOfCurrentDay + minutesFromMidnightToFarExpiryTime + daysToExpiryFarExpiry) / expiryTTE365Dminutes
    #nearExpiryTTE = 0.068348554
    #farExpiryTTE = 0.088268645
    if printResults:
        print("nearExpiryTTE: " + str(nearExpiryTTE))
        print("farExpiryTTE: " + str(farExpiryTTE))
        print("minutesToMidnightOfCurrentDay: " + str(minutesToMidnightOfCurrentDay))
        print("minutesFromMidnightToFarExpiryTime: " + str(minutesFromMidnightToFarExpiryTime))
        print("daysToExpiryFarExpiry: " + str(daysToExpiryFarExpiry))

    nearExpiry1M_USTreasury = False
    farExpiry1M_USTreasury = False
    nearExpiry3M_USTreasury = False
    farExpiry3M_USTreasury = False
    ## Interest Rate (need to use 30day/1month T-Bill bond equivalent rate for both expiries)
    if nearExpiryTTE < (2*60)/360:
        nearExpiry1M_USTreasury = True
    else:
        nearExpiry3M_USTreasury = True
        
    if farExpiryTTE < (2*60)/360:
        farExpiry1M_USTreasury = True
    else:
        farExpiry3M_USTreasury = True

    if nearExpiry1M_USTreasury or farExpiry1M_USTreasury:
        #get 1M US T-Bill rate
        cur = con.cursor()
        qry = "Select 1M from USTreasuryYields where quote_date = '%s'" % quote_date
        cur.execute(qry)
        OneM_USTreasuryResultsTemp = cur.fetchall()
        OneM_USTreasuryResults = OneM_USTreasuryResultsTemp[0][0]
        cur.close()
        
    if nearExpiry3M_USTreasury or farExpiry3M_USTreasury:
         # get 3M US T-Bill rate
        cur = con.cursor()
        qry = "Select 3M from USTreasuryYields where quote_date = '%s'" % quote_date
        cur.execute(qry)
        ThreeM_USTreasuryResultsTemp = cur.fetchall()
        ThreeM_USTreasuryResults = ThreeM_USTreasuryResultsTemp[0][0]
        cur.close()
        
    if nearExpiry1M_USTreasury:
        nearExpiryInterestRate = OneM_USTreasuryResults
    else:
        nearExpiryInterestRate = ThreeM_USTreasuryResults
        
    if farExpiry1M_USTreasury:
        farExpiryInterestRate = OneM_USTreasuryResults
    else:
        farExpiryInterestRate = ThreeM_USTreasuryResults

    if printResults:
        print("nearExpiryInterestRate :" + str(nearExpiryInterestRate))
        print("farExpiryInterestRate :" + str(farExpiryInterestRate))
##    nearExpiryInterestRate = 0.000305
##    farExpiryInterestRate = 0.000286
    #sys.exit(0)
    ## Determine the forward SPX level where min(abs(c_avgBidAsk - p_avgBidAsk))
    nearExpiryForwardRow = min(nearExpiryListSorted,key=itemgetter(f("callLessPutTheo")))
    nearExpiryForward = nearExpiryForwardRow[f("strike")]
    nearExpiryForwardIndex = nearExpiryForward + math.exp(nearExpiryTTE * nearExpiryInterestRate) * (nearExpiryForwardRow[f("c_avgBidAsk")] - nearExpiryForwardRow[f("p_avgBidAsk")])

    farExpiryForwardRow = min(farExpiryListSorted,key=itemgetter(f("callLessPutTheo")))
    farExpiryForward = farExpiryForwardRow[f("strike")]
    farExpiryForwardIndex = farExpiryForward + math.exp(farExpiryTTE * farExpiryInterestRate) * (farExpiryForwardRow[f("c_avgBidAsk")] - farExpiryForwardRow[f("p_avgBidAsk")])

    if printResults:
        print("nearExpiryStrike: " + str(nearExpiryForward))
        print("farExpiryStrike: " + str(farExpiryForward))

        print("nearExpiryForwardIndex: " + str(nearExpiryForwardIndex))
        print("farExpiryForwardIndex: " + str(farExpiryForwardIndex))

    ## determine the strike immediately below the forwardIndex
    nearExpiryForwardIndexIndex = bisect.bisect([row[f("strike")] for row in nearExpiryListSorted], nearExpiryForwardIndex)
    nearExpiryK0Strike = nearExpiryListSorted[nearExpiryForwardIndexIndex-1][f("strike")]

    farExpiryForwardIndexIndex = bisect.bisect([row[f("strike")] for row in farExpiryListSorted], farExpiryForwardIndex)
    farExpiryK0Strike = farExpiryListSorted[farExpiryForwardIndexIndex-1][f("strike")]

    if printResults:
        print("nearExpiryK0Strike: " + str(nearExpiryK0Strike))
        print("farExpiryK0Strike: " + str(farExpiryK0Strike))

    ## Select puts with strike below K0 and work downwards, exclude any put with bid price == 0, once two consecutive puts have zero bid price, ignore all lower strikes
    def isolateStrikes(expiryList, columnName, countZeroBidPrices):
        zeroBidCheckList = list()
        for row in expiryList:
            if row[f(columnName)] == 0: # check the bid price is zero
                countZeroBidPrices += 1
    ##            if countZeroBidPrices < 2:
    ##                continue # don't include this strike, go back to loop
    ##            else:
    ##                return zeroBidCheckList # we have 2 consecutive bid prices of zero and stop adding strikes
            else:
                zeroBidCheckList.append(row) # bid price is non zero to add it
                countZeroBidPrices = 0 # reset counter to zero
            if countZeroBidPrices > 1:
                return zeroBidCheckList
        return zeroBidCheckList

    nearExpiryListSortedReverse = sorted(nearExpiryListSorted, key=lambda student: student[f("strike")], reverse=True)
    nearExpiryPutList = [t for t in nearExpiryListSortedReverse if t[f("strike")] < nearExpiryK0Strike] # get all strikes below K0, starting with strike immediately below K0 and decreasing
    countZeroBidPrices = 0
    nearExpiryPutListZeroBidChecked = list()
    nearExpiryPutListZeroBidChecked = isolateStrikes(nearExpiryPutList, "p_bid", countZeroBidPrices)

    farExpiryListSortedReverse = sorted(farExpiryListSorted, key=lambda student: student[f("strike")], reverse=True)
    farExpiryPutList = [t for t in farExpiryListSortedReverse if t[f("strike")] < farExpiryK0Strike] # get all strikes below K0, starting with strike immediately below K0 and decreasing
    countZeroBidPrices = 0
    farExpiryPutListZeroBidChecked = list()
    farExpiryPutListZeroBidChecked = isolateStrikes(farExpiryPutList, "p_bid", countZeroBidPrices)

    nearExpiryCallList = [t for t in nearExpiryListSorted if t[f("strike")] > nearExpiryK0Strike] # get all strikes above K0, starting with strike immediately above K0 and increasing
    countZeroBidPrices = 0
    nearExpiryCallListZeroBidChecked = list()
    nearExpiryCallListZeroBidChecked = isolateStrikes(nearExpiryCallList, "c_bid", countZeroBidPrices)

    farExpiryCallList = [t for t in farExpiryListSorted if t[f("strike")] > farExpiryK0Strike] # get all strikes above K0, starting with strike immediately above K0 and increasing
    countZeroBidPrices = 0
    farExpiryCallListZeroBidChecked = list()
    farExpiryCallListZeroBidChecked = isolateStrikes(farExpiryCallList, "c_bid", countZeroBidPrices)

    nearExpiryK0RowTemp = [t for t in nearExpiryListSorted if t[f("strike")] == nearExpiryK0Strike]
    nearExpiryK0Row = nearExpiryK0RowTemp[0]

    farExpiryK0RowTemp = [t for t in farExpiryListSorted if t[f("strike")] == farExpiryK0Strike]
    farExpiryK0Row = farExpiryK0RowTemp[0]

    def calculateExpiryVarianceContribution(theList, r, T, columnHeader):
        for i in range(len(theList)):
            if i == 0:
                deltaStrike = abs(theList[i][f("strike")] - theList[i+1][f("strike")])
            elif i == len(theList)-1: # last in list
                deltaStrike = abs(theList[i][f("strike")] - theList[i-1][f("strike")])
            else:
                deltaStrike = abs(theList[i-1][f("strike")] - theList[i+1][f("strike")])/2 # average of strike on either side
            strikeContribution = deltaStrike / math.pow(theList[i][f("strike")], 2) * math.exp(r*T) * theList[i][f(columnHeader)]
            theList[i].append(strikeContribution)
        return theList

    nearExpiryPutListZeroBidCheckedContribution = calculateExpiryVarianceContribution(nearExpiryPutListZeroBidChecked, nearExpiryInterestRate, nearExpiryTTE, "p_avgBidAsk")
    farExpiryPutListZeroBidCheckedContribution = calculateExpiryVarianceContribution(farExpiryPutListZeroBidChecked, farExpiryInterestRate, nearExpiryTTE, "p_avgBidAsk")

    nearExpiryCallListZeroBidCheckedContribution = calculateExpiryVarianceContribution(nearExpiryCallListZeroBidChecked, nearExpiryInterestRate, nearExpiryTTE, "c_avgBidAsk")
    farExpiryCallListZeroBidCheckedContribution = calculateExpiryVarianceContribution(farExpiryCallListZeroBidChecked, farExpiryInterestRate, nearExpiryTTE, "c_avgBidAsk")

    nearExpiryK0StrikeDelta = (nearExpiryCallListZeroBidCheckedContribution[0][f("strike")] - nearExpiryPutListZeroBidCheckedContribution[0][f("strike")] ) / 2
    nearExpiryK0Contribution = nearExpiryK0StrikeDelta / math.pow(nearExpiryK0Strike, 2) * math.exp(nearExpiryInterestRate * nearExpiryTTE) * (nearExpiryK0Row[f("c_avgBidAsk")] + nearExpiryK0Row[f("p_avgBidAsk")])/2
    nearExpiryK0Row.append(nearExpiryK0Contribution)


    farExpiryK0StrikeDelta = (farExpiryCallListZeroBidCheckedContribution[0][f("strike")] - farExpiryPutListZeroBidCheckedContribution[0][f("strike")] ) / 2
    farExpiryK0Contribution = farExpiryK0StrikeDelta / math.pow(farExpiryK0Strike, 2) * math.exp(farExpiryInterestRate * farExpiryTTE) * (farExpiryK0Row[f("c_avgBidAsk")] + farExpiryK0Row[f("p_avgBidAsk")])/2
    farExpiryK0Row.append(farExpiryK0Contribution)

    def calculateExpiryVariance(theList, T, K0, F):
        forwardAdjust = math.pow(F / K0 - 1, 2) / T
        contributionSum = [sum(i) for i in zip(*theList)] # sum over all columns
        #print("VarianceContribution: " + str(contributionSum[f("varianceContribution")]))
        #print("VarianceContributionTimeScaled :" + str(2 / T * contributionSum[f("varianceContribution")] ))
        #print("Forward Adjust: " + str(forwardAdjust))
        return 2 / T * contributionSum[f("varianceContribution")] - forwardAdjust

    # combine puts, calls and K0 together
    nearExpiryContributionList = list()
    nearExpiryContributionList.extend(nearExpiryPutListZeroBidCheckedContribution)
    nearExpiryContributionList.extend(nearExpiryCallListZeroBidCheckedContribution)
    nearExpiryContributionList.append(nearExpiryK0Row)
    nearExpiryVariance = calculateExpiryVariance(nearExpiryContributionList, nearExpiryTTE, nearExpiryK0Row[f("strike")], nearExpiryForwardIndex)
    if printResults:
        print("nearExpiryVariance: " + str(nearExpiryVariance))

    farExpiryContributionList = list()
    farExpiryContributionList.extend(farExpiryPutListZeroBidCheckedContribution)
    farExpiryContributionList.extend(farExpiryCallListZeroBidCheckedContribution)
    farExpiryContributionList.append(farExpiryK0Row)
    farExpiryVariance = calculateExpiryVariance(farExpiryContributionList, farExpiryTTE, farExpiryK0Row[f("strike")], farExpiryForwardIndex)
    if printResults:
        print("farExpiryVariance: " + str(farExpiryVariance))

    # Calculate VIX
    nearExpiryTTEminutes = nearExpiryTTE * expiryTTE365Dminutes
    farExpiryTTEminutes = farExpiryTTE * expiryTTE365Dminutes

    nearExpiryTimeFraction = (farExpiryTTEminutes - expiryTTE30Dminutes) / (farExpiryTTEminutes - nearExpiryTTEminutes)
    if printResults:
        print("nearExpiryTimeFraction: " + str(nearExpiryTimeFraction))
    farExpiryTimeFraction = 1 - nearExpiryTimeFraction
    scaleTo365D = expiryTTE365Dminutes / expiryTTE30Dminutes

    nearVixCalc = nearExpiryTTE * nearExpiryVariance * nearExpiryTimeFraction
    farVixCalc = farExpiryTTE * farExpiryVariance * farExpiryTimeFraction
    VIX = 100 * math.pow((nearVixCalc + farVixCalc) * scaleTo365D, 0.5)
    if printResults:
        print("VIX: " + str(VIX))
    return VIX
