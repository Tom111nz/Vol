## Calculate VIX and save into database
from VIXFutureOptionExpiryList import VIXFutureOptionExpiryList
from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
import sys
import MySQLdb as mdb
import datetime
from dateutil.parser import parse

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")
#DeltaUsed = 0.7
InterestRateUsed = 0.01
calculateVIXFromSingleExpiry_PrintResults = False
rowsInserted = 0


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
for item in VIXFutureOptionExpiryList():
    expiriesAlreadyInList.append(datetime.datetime.strptime(item[2] + ' 08:30:00', "%Y-%m-%d %H:%M:%S"))

outer = set(expiriesList) - set(expiriesAlreadyInList)
if len(outer) > 0:
    print('List of option expiries not yet in VIXFutureOptionExpiryList')
    for item in sorted(outer):
        print(item)


for sheetNum, row in enumerate(VIXFutureOptionExpiryList()):
    
    FuturesContract = row[0]
    futureExpiryString = row[1]
    futureExpiryDatetime = datetime.datetime.strptime(futureExpiryString, "%Y-%m-%d")
    optionExpiryString = row[2] + ' 08:30:00'
    optionExpiryDatetime = datetime.datetime.strptime(optionExpiryString, "%Y-%m-%d %H:%M:%S")

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
            ## check is not in database already
            checkSQL = ('Select * from VIXCalculated where quote_date = '"'%s'"' and FuturesContract = '"'%s'"' and OptionExpiration = '"'%s'"' and InterestRateUsed = '"'%s'"''  %
                        (quoteDateKey, FuturesContract, optionExpiryString, InterestRateUsed))
            cur = con.cursor()
            cur.execute(checkSQL)
            if cur.fetchone() is None:              
                VIXCalculated = calculateVIXFromSingleExpiry(quoteDateKey, optionExpiryString, InterestRateUsed, calculateVIXFromSingleExpiry_PrintResults)
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
