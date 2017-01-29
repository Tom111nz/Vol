## Copy folder from Anaconda at:
#anaconda/pkgs/pandas-0.18/lib/python3.5/site-packages/pandas/
#and this file at same directory: site-packages/pandas-0.18.1-py3.5.egg-info/
# and copy folder(s) to:
## MacIntosh HD/Library\Frameworks\Python.framework\Versions\3.5\lib\python3.5\site-packages\
import MySQLdb as mdb
import numpy as np
import csv
import os
path = os.path.dirname(mdb.__file__)
print(path)
import nose
import numpy
path = os.path.dirname(numpy.__file__)
print(path)
import pandas as pd
path = os.path.dirname(pd.__file__)
print(path)
s = pd.Series([1,3,5,np.nan,6,8])
print(s)
#pd.test()
##import importlib.util
##spec = importlib.util.spec_from_file_location("pandas", "/path/to/file.py")
##import \\users\tomobrien\anaconda\bin\pandas as pd
#print(pandas.version.version)
import sys
import numpy as np
print(sys.version)
import pip
installed_packages = pip.get_installed_distributions()
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
     for i in installed_packages])
print(installed_packages_list)

con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")

sqlQuery = ('select oe.quote_date, oe.Expiration, st.strike, st.option_type, og.delta_1545, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545, og.vega_1545, abs(0.5 - og.delta_1545), abs(0.7 - og.delta_1545)  from optiongreeks og ' 
    'join optionexpiry oe on oe.ID = og.optionexpiryID '
    'join strike st on st.ID = og.strikeID '
    'where oe.ID in '
    '( '
    'select ID from optionexpiry where rootOriginal in ("SPX") and expiration = '"'2016-10-21 08:30:00'"' '
    ') '
    'and st.option_type = '"'c'"' '
    'order by oe.quote_date, oe.Expiration, st.strike;')

cur = con.cursor()
cur.execute(sqlQuery)
strikeDataRaw = cur.fetchall()
cur.close()

print(len(strikeDataRaw))
##arr = np.empty((1,10))
##print(arr)
strikeDataRawList =[]
for row in strikeDataRaw:
    aList = []
    aList.append(row[0])
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
    aList.append(row[11])
    strikeDataRawList.append(aList)
##    print(row)
##    arr = np.append(arr, np.array((row)), axis=0)
##for row in strikeDataRawList[:10]:
##    print(row)
##sys.exit(0)
# loop through quote_dates and find the 50 delta row
strikeDataRawHeaders = ['quote_raw', 'expiration', 'strike', 'option_type', 'delta', 'bid', 'ask', 'mid', 'imp_vol', 'vega', 'deltaless0.5', 'deltaless0.7']
df = pd.DataFrame(strikeDataRawList, columns=strikeDataRawHeaders)
# 50 delta
idx50 = df.groupby(df['quote_raw'])['deltaless0.5'].idxmin()
closest50DStrike = df.loc[idx50, ['quote_raw', 'expiration', 'strike', 'option_type', 'delta', 'imp_vol', 'vega', 'deltaless0.5', 'deltaless0.7']]
# 70 delta
idx70 = df.groupby(df['quote_raw'])['deltaless0.7'].idxmin()
closest70DStrike = df.loc[idx70, ['quote_raw', 'expiration', 'strike', 'option_type', 'delta', 'imp_vol', 'vega', 'deltaless0.5', 'deltaless0.7']]

closest50DStrike.to_csv('tester.csv', sep=' ')
closest70DStrike.to_csv('tester70.csv', sep=' ')

