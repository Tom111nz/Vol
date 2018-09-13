## Copy folder from Anaconda at:
#anaconda/pkgs/pandas-0.18/lib/python3.5/site-packages/pandas/
#and this file at same directory: site-packages/pandas-0.18.1-py3.5.egg-info/
# and copy folder(s) to:
## MacIntosh HD/Library\Frameworks\Python.framework\Versions\3.5\lib\python3.5\site-packages\
import MySQLdb as mdb
import numpy as np
import csv
import os
import sys
import nose
import pandas as pd
import datetime
#path = os.path.dirname(mdb.__file__)
#print(path)
#path = os.path.dirname(numpy.__file__)
#print(path)
#path = os.path.dirname(pd.__file__)
#print(path)
#s = pd.Series([1,3,5,np.nan,6,8])
#print(s)
#pd.test()
##import importlib.util
##spec = importlib.util.spec_from_file_location("pandas", "/path/to/file.py")
##import \\users\tomobrien\anaconda\bin\pandas as pd
#print(pandas.version.version)
#print(sys.version)
##import pip
##installed_packages = pip.get_installed_distributions()
##installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
##     for i in installed_packages])
##print(installed_packages_list)

def getDeltaThroughTime(expiration, deltaTarget, optionType):
    con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")

    sqlQuery = ('select oe.quote_date, oe.Expiration, st.strike, st.option_type, og.delta_1545, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545, og.vega_1545, '
        'case when st.option_type = "c" then abs(%s - delta_1545) else abs(%s - (1-abs(delta_1545))) end as "delta_gap" from optiongreeks og ' 
        'join optionexpiry oe on oe.ID = og.optionexpiryID '
        'join strike st on st.ID = og.strikeID '
        'where oe.ID in '
        '( '
        'select ID from optionexpiry where root in ("SPX") and expiration = '"'%s'"' '
        ') '
        'and st.option_type = '"'%s'"' '
        'order by oe.quote_date, oe.Expiration, st.strike;' % (deltaTarget, deltaTarget, expiration, optionType))

    cur = con.cursor()
    cur.execute(sqlQuery)
    strikeDataRaw = cur.fetchall()
    cur.close()

    #print(len(strikeDataRaw))
    ##arr = np.empty((1,10))
    ##print(arr)
    strikeDataRawList =[]
    for row in strikeDataRaw:
        aList = []
        aList.append(datetime.datetime.strftime(row[0], "%Y-%m-%d"))
        aList.append(row[1])
        aList.append(row[2])
        aList.append(row[3])
        aList.append(row[4])
        aList.append(row[5])
        aList.append(row[6])
        aList.append(row[7])
        aList.append(row[8])
        aList.append(row[9])
        aList.append(row[10])
        strikeDataRawList.append(aList)
    ##    print(row)
    ##    arr = np.append(arr, np.array((row)), axis=0)
    ##for row in strikeDataRawList[:10]:
    ##    print(row)
    ##sys.exit(0)
    # loop through quote_dates and find the 50 delta row
    strikeDataRawHeaders = ['quote_raw', 'expiration', 'strike', 'option_type', 'delta', 'bid', 'ask', 'mid', 'imp_vol', 'vega', 'deltalessX']
    df = pd.DataFrame(strikeDataRawList, columns=strikeDataRawHeaders)
    # X delta
    idxX = df.groupby(df['quote_raw'])['deltalessX'].idxmin()
    closestXDStrike = df.loc[idxX, strikeDataRawHeaders]
    ## output to csv
    #closestXDStrike.to_csv('tester70.csv', sep=' ')
##    for key, value in closestXDStrike.set_index('quote_raw').T.to_dict('list').items():
##        print(key)
##        print(value)
    print('######### exit function')
    #return closest70DStrike.set_index('quote_raw')['mid'].to_dict()
    return closestXDStrike.set_index('quote_raw').T.to_dict('list')
