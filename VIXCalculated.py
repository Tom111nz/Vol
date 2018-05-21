## Calculate VIX and save into database
from VIXFutureOptionExpiryList import VIXFutureOptionExpiryList
from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
import sys
import MySQLdb as mdb
import datetime
from dateutil.parser import parse

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")
DeltaUsed = 0.7
InterestRateUsed = 0.01
calculateVIXFromSingleExpiry_PrintResults = False
for sheetNum, row in enumerate(VIXFutureOptionExpiryList()):
    
    FuturesContract = row[0]
    futureExpiryString = row[1]
    futureExpiryDatetime = datetime.datetime.strptime(futureExpiryString, "%Y-%m-%d")
    optionExpiryString = row[2] + ' 08:30:00'
    optionExpiryDatetime = datetime.datetime.strptime(optionExpiryString, "%Y-%m-%d %H:%M:%S")

    ## break if is an old contract
    if optionExpiryDatetime.year < 2018:
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

    for row in quoteDatesOptionsRaw:
        quoteDate = row[0]
        if datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) <= datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day):
            quoteDateKey = datetime.datetime.strftime(quoteDate, "%Y-%m-%d")
            ## check is not in database already
            checkSQL = ('Select * from VIXCalculated where quote_date = '"'%s'"' and FuturesContract = '"'%s'"' and OptionExpiration = '"'%s'"' and InterestRateUsed = '"'%s'"' and DeltaUsed = '"'%s'"'' %
                        (quoteDateKey, FuturesContract, optionExpiryString, InterestRateUsed, DeltaUsed))
            cur = con.cursor()
            cur.execute(checkSQL)
            if cur.fetchone() is None:              
                VIXCalculated = calculateVIXFromSingleExpiry(quoteDateKey, optionExpiryString, InterestRateUsed, calculateVIXFromSingleExpiry_PrintResults)
                cur.execute('''INSERT into VIXCalculated (quote_date, FuturesContract, OptionExpiration, InterestRateUsed, DeltaUsed, VIXCalculated)
                          values (%s, %s, %s, %s, %s, %s)''',
                          (parse(quoteDateKey).strftime("%Y-%m-%d %H:%M:%S"), FuturesContract, optionExpiryString, InterestRateUsed, DeltaUsed, VIXCalculated))
                cur.close()
                con.commit()
            else:
                cur.close()
