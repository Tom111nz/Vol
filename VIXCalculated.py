## Calculate VIX and save into database
from VIXFutureOptionExpiryList import VIXFutureOptionExpiryList
from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
import sys
#import MySQLdb as mdb
import pymysql as mdb
import datetime
from dateutil.parser import parse
from InterpolateUSYield import interpolateUSYield

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol", port = 3307)
#DeltaUsed = 0.7
#InterestRateUsed = 0.01
calculateVIXFromSingleExpiry_PrintResults = False
calculateVIXFromSingleExpiry_use30DaysToExpiry = False
rowsInserted = 0

# generate the required VIX Futures contract string
def generateVIXFuturesString(optionExpiryDatetime):
    # create the VIX futures contract string for a given option expiry
    theOptionMonth = optionExpiryDatetime.month
    theOptionYear = optionExpiryDatetime.year - 2000
##    print('theOptionMonth ' + str(theOptionMonth))
##    print('theOptionYear ' + str(theOptionYear))
    if theOptionMonth == 1:
        if theOptionYear - 1 < 10:
            result = 'Z (Dec 0' + str(theOptionYear - 1) + ')'
        else:
            result = 'Z (Dec ' + str(theOptionYear - 1) + ')'
    elif theOptionMonth == 2:
        if theOptionYear < 10:
            result = 'F (Jan 0' + str(theOptionYear) + ')'
        else:
            result = 'F (Jan ' + str(theOptionYear) + ')'
    elif theOptionMonth == 3:
        if theOptionYear < 10:
            result = 'G (Feb 0' + str(theOptionYear) + ')'
        else:
            result = 'G (Feb ' + str(theOptionYear) + ')'
    elif theOptionMonth == 4:
        if theOptionYear < 10:
            result = 'H (Mar 0' + str(theOptionYear) + ')'
        else:
            result = 'H (Mar ' + str(theOptionYear) + ')'
    elif theOptionMonth == 5:
        if theOptionYear < 10:
            result = 'J (Apr 0' + str(theOptionYear) + ')'
        else:
            result = 'J (Apr ' + str(theOptionYear) + ')'
    elif theOptionMonth == 6:
        if theOptionYear < 10:
            result = 'K (May 0' + str(theOptionYear) + ')'
        else:
            result = 'K (May ' + str(theOptionYear) + ')'
    elif theOptionMonth == 7:
        if theOptionYear < 10:
            result = 'M (Jun 0' + str(theOptionYear) + ')'
        else:
            result = 'M (Jun ' + str(theOptionYear) + ')'
    elif theOptionMonth == 8:
        if theOptionYear < 10:
            result = 'N (Jul 0' + str(theOptionYear) + ')'
        else:
            result = 'N (Jul ' + str(theOptionYear) + ')'
    elif theOptionMonth == 9:
        if theOptionYear < 10:
            result = 'Q (Aug 0' + str(theOptionYear) + ')'
        else:
            result = 'Q (Aug ' + str(theOptionYear) + ')'
    elif theOptionMonth == 10:
        if theOptionYear < 10:
            result = 'U (Sep 0' + str(theOptionYear) + ')'
        else:
            result = 'U (Sep ' + str(theOptionYear) + ')'
    elif theOptionMonth == 11:
        if theOptionYear < 10:
            result = 'V (Oct 0' + str(theOptionYear) + ')'
        else:
            result = 'V (Oct ' + str(theOptionYear) + ')'
    elif theOptionMonth == 12:
        if theOptionYear < 10:
            result = 'X (Nov 0' + str(theOptionYear) + ')'
        else:
            result = 'X (Nov ' + str(theOptionYear) + ')'
    else:
        result = 'MassiveError!'

    return result


## check we are not missing an option expiry in VIXFutureOptionExpiryList()
sqlExpiries = ('select expiration from optionexpiry '
            'where quote_date = (select max(quote_date) from optionexpiry) '
            'and root = "SPX"')
cur = con.cursor()
cur.execute(sqlExpiries)
expiries = cur.fetchall()
cur.close()
expiriesList = list()
expiriesAlreadyInList = list()
for item in expiries:
    expiriesList.append(item[0])
##for item in VIXFutureOptionExpiryList():
##    expiriesAlreadyInList.append(datetime.datetime.strptime(item[2] + ' 08:30:00', "%Y-%m-%d %H:%M:%S"))
##
##outer = set(expiriesList) - set(expiriesAlreadyInList)
##if len(outer) > 0:
##    print('List of option expiries not yet in VIXFutureOptionExpiryList')
##    for item in sorted(outer):
##        print(item)


#for sheetNum, row in enumerate(VIXFutureOptionExpiryList()):
for sheetNum, row in enumerate(expiriesList):    
    #FuturesContract = row[0]
    #futureExpiryString = row[1]
    #futureExpiryDatetime = datetime.datetime.strptime(futureExpiryString, "%Y-%m-%d")
    #optionExpiryString = row[2] + ' 08:30:00'
    optionExpiryDatetime = row
    optionExpiryString = optionExpiryDatetime.strftime("%Y-%m-%d %H:%M:%S")
    #optionExpiryDatetime = datetime.datetime.strptime(row, "%Y-%m-%d %H:%M:%S")
    FuturesContract = generateVIXFuturesString(optionExpiryDatetime)
##    # test formula
##    generateVIXFuturesString(optionExpiryDatetime)
##    sys.exit(0)

    
    ## break if is an old contract
    sqlEarliestExpiry = ('select min(expiration) from optionexpiry '
                'where quote_date = (select max(quote_date) from optionexpiry) '
                'and root = "SPX"')
    cur = con.cursor()
    cur.execute(sqlEarliestExpiry)
    earliestExpiry = cur.fetchone()
    cur.close()
    if optionExpiryDatetime < earliestExpiry[0]: ## process from the earliest option expiry, and onwards       
        continue
## Get days where data exists for the option expiry
    sqlQuery = ('select oe.quote_date, und.underlying_bid_1545 from OptionExpiry oe '
                'left join underlying und on oe.id = und.optionexpiryid '
                'where oe.root = "SPX" '
                'and oe.expiration = '"'%s'"' '
                'group by oe.quote_date order by oe.quote_date;' % optionExpiryString)
    cur = con.cursor()
    cur.execute(sqlQuery)
    quoteDatesOptionsRaw = cur.fetchall()
    cur.close()
    print('Option expiries that we calculate a VIX for')
    for row in quoteDatesOptionsRaw:
        quoteDate = row[0]
        if datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) <= datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day):
            quoteDateKey = datetime.datetime.strftime(quoteDate, "%Y-%m-%d")
            InterestRateUsed = interpolateUSYield(quoteDate, optionExpiryDatetime)
            ## check is not in database already
            checkSQL = ('Select * from VIXCalculated where quote_date = '"'%s'"' and FuturesContract = '"'%s'"' and OptionExpiration = '"'%s'"''  %
                        (quoteDateKey, FuturesContract, optionExpiryString))
            cur = con.cursor()
            cur.execute(checkSQL)
            if cur.fetchone() is None:              
                VIXCalculated = calculateVIXFromSingleExpiry(quoteDateKey, optionExpiryString, InterestRateUsed, calculateVIXFromSingleExpiry_PrintResults, calculateVIXFromSingleExpiry_use30DaysToExpiry)
                cur.execute('''INSERT into VIXCalculated (quote_date, FuturesContract, OptionExpiration, InterestRateUsed, VIXCalculated)
                          values (%s, %s, %s, %s, %s)''',
                          (parse(quoteDateKey).strftime("%Y-%m-%d %H:%M:%S"), FuturesContract, optionExpiryString, InterestRateUsed, VIXCalculated))
                cur.close()
                con.commit()
                print(str(optionExpiryDatetime))
                rowsInserted = rowsInserted + 1
            else:
                cur.close()
print('VIXCalculated inserted %s rows' % str(rowsInserted)) 
