#import MySQLdb as mdb
import pymysql as mdb
import datetime

def interpolateUSYield(quoteDateDateTime, optionExpiryDatetime):
    con = mdb.connect(host="localhost",user="root",
                      passwd="password",db="Vol", port = 3307)
    #### We exclude the 30Y point because it is sometimes blank, and we never need it anyway
    quoteDateDateTimeIterated = quoteDateDateTime
    sqlResults = None
    try:
        while sqlResults is None: # needs to work the first time through
            sqlQuery = ('select 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y from USTreasuryYields where quote_date = '"'%s'"';' % datetime.datetime.strftime(quoteDateDateTimeIterated, "%Y-%m-%d"))  
            cur = con.cursor()
            cur.execute(sqlQuery)
            #print('cur.fetchone() ')
            #print(cur.fetchone())
            #print('quoteDateDateTimeIterated: ' + str(quoteDateDateTimeIterated))
            sqlResults = cur.fetchone()
            cur.close()
            if sqlResults:
                # count the number of nones
                noneCount = 0
                totalCount = 0
                for row in sqlResults:
                    totalCount = totalCount + 1
                    if row is None:
                        noneCount = noneCount + 1
                if totalCount - noneCount > 1: # need at least two non-null interest rate to interpolate below
                    break
                else:
                    sqlResults = None
                    quoteDateDateTimeIterated = quoteDateDateTimeIterated + datetime.timedelta(days=1) # add a day until we get yield curve data
                    continue
            else:
                sqlResults = None # to reiterate
                quoteDateDateTimeIterated = quoteDateDateTimeIterated + datetime.timedelta(days=1) # add a day until we get yield curve data
                continue
            #quoteDateDateTimeIterated = quoteDateDateTimeIterated + datetime.timedelta(days=1) # add a day until we get yield curve data
            
#            if cur.fetchone() is not None:
#                print('Not none!')
#                sqlResults = cur.fetchone()
#                break
                
        #print('Got here')
        sqlQuery = ('select 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y from USTreasuryYields where quote_date = '"'%s'"';' % datetime.datetime.strftime(quoteDateDateTimeIterated, "%Y-%m-%d"))  
        cur = con.cursor()
        cur.execute(sqlQuery)
        sqlResults = cur.fetchall()
        cur.close()
#        print('sqlResults')
#        print(sqlResults)
#        print(quoteDateDateTimeIterated)
        yieldsListOriginal = sqlResults[0]
        aMonth = 30.0/360.0 # US day count conventions
        TTEListOriginal = [aMonth, 3*aMonth, 6*aMonth, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0]
        # Remove any nulls
        yieldsList = list()
        TTEList = list()
        for a,b in zip(yieldsListOriginal, TTEListOriginal):
            if a is not None: # remove the nulls from both lists
                yieldsList.append(a)
                TTEList.append(b)
                
        #yieldsList = [x for x in yieldsList if not None]
        
        
        
        
        
    #    for row in sqlResults[0]:
    #        print(row)
    #    for row in TTEList:
    #        print(row)
        calendarTTE = max(((optionExpiryDatetime - quoteDateDateTime).total_seconds())/(60*60*24*365), 0.002739) # assume 365 days/year (floor at 1 calendar day)
    #    print(calendarTTE)
    #    print(quoteDateDateTime)
    #    print(optionExpiryDatetime)
    ##    print(calendarTTE)
        # find the first entry in the TTEList equal to or smaller than calendarTTE
        locAbove = next(x[0] for x in enumerate(TTEList) if x[1] >= calendarTTE)
        locBelow = locAbove - 1
        slope = (yieldsList[locAbove] - yieldsList[locBelow])/(TTEList[locAbove] - TTEList[locBelow])
        return yieldsList[locBelow] + slope * (calendarTTE - TTEList[locBelow])
    except Exception as inst:
        print(type(inst))     # the exception instance
        print(inst.args)      # arguments stored in .args
        print(inst)           # __str__ allows args to be printed directly
        print('Error in interpolateUSYield')
        print(sqlQuery)
        print('quoteDateDateTime: ' + str(quoteDateDateTime))
        print('optionExpiryDatetime: ' + str(optionExpiryDatetime))
    else:
        print('Error in interpolateUSYield')
        print(sqlQuery)
        print('quoteDateDateTime: ' + str(quoteDateDateTime))
        print('optionExpiryDatetime: ' + str(optionExpiryDatetime))

#aYield = interpolateUSYield(datetime.date(2010, 10, 11), datetime.date(2010, 12, 18))
#print(aYield)
