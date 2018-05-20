## Calculate VIX and save into database
from VIXFutureOptionExpiryList import VIXFutureOptionExpiryList
import sys
##print(VIXFutureOptionExpiryList)
##VIXFutureOptionExpiryList = VIXFutureOptionExpiryList()
##for row in VIXFutureOptionExpiryList:
##    print(row)

##(1) put rules around db table (database unique key: everythig except the VIXCalculated)
##(2) check value is not already in db


DeltaUsed = 0.7
InterestRateUsed = 0.01
calculateVIXFromSingleExpiry_PrintResults = False
for sheetNum, row in enumerate(VIXFutureOptionExpiryList()):
    
    FuturesContract = row[0]
    futureExpiryString = row[1]
    futureExpiryDatetime = datetime.datetime.strptime(futureExpiryString, "%Y-%m-%d")
    optionExpiryString = row[2] + ' 08:30:00'
    optionExpiryDatetime = datetime.datetime.strptime(optionExpiryString, "%Y-%m-%d %H:%M:%S")

## Get days where daya exoists for the option expiry
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
        if datetime.datetime(quoteDate.year, quoteDate.month, quoteDate.day) <= datetime.datetime(optionExpiryDatetime.year, optionExpiryDatetime.month, optionExpiryDatetime.day):
            quoteDateKey = datetime.datetime.strftime(quoteDate, "%Y-%m-%d")
            VIXCalculated = calculateVIXFromSingleExpiry(quoteDateKey, optionExpiryString, InterestRateUsed, calculateVIXFromSingleExpiry_PrintResults)

            cur.execute('''INSERT into VIXCalculated (quote_date, Contract, OptionExpiryID, InterestRateUsed, DeltaUsed, VIXCalculated)
                          values (%s, %s, %s, %s, %s, %s)''',
                          (parse(quoteDateKey).strftime("%Y-%m-%d %H:%M:%S"), FuturesContract, optionExpiryString, InterestRateUsed, DeltaUsed, VIXCalculated))
