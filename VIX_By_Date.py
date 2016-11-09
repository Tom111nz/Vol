## Loop through and calculate VIX
import MySQLdb as mdb
import datetime
import sys
from Replicate_VIX_Calculation import calculateVIX 

con = mdb.connect(host="localhost",user="root",
                      passwd="password",db="Vol")
cur = con.cursor()

calculateVIX('2016-09-20', True)
sys.exit(0)

query = 'select TradeDate, clos from VIX where tradeDate > "2014-01-01"'
cur.execute(query)
VixDatesRaw = cur.fetchall()
cur.close()

VixActual = {}
try: 
    for row in VixDatesRaw:
        aRow = list(row)
    ##    print(aRow)
    ##    print(aRow[0])
    ##    print(aRow[1])
        VixActual[aRow[0]] = [0]*3
        vixValues = VixActual.get(aRow[0])
        vixValues[0] = float(aRow[1])
        try:
            vixValues[1] = calculateVIX(str(aRow[0]))
            vixValues[2] = vixValues[1] - vixValues[0]
        except Exception as err:
            #print("No VIX for: " + str(aRow[0]))
            vixValues[2] = -3       
        print(str(aRow[0]) + ":" + str(vixValues[2]) + ":" + str(vixValues[0]) + ":" + str(vixValues[1]))
    ##    print("VixValues")
    ##    print(vixValues)
        VixActual[aRow[0]] = vixValues
except (RuntimeError, TypeError, NameError):
    for key, value in VixActual:
        print(str(key) + " :" + str(value[2]))
print("Finished")
##vixResults = {}
##for d in VixDates:
##    vixResults[d] = calculateVIX(d)
##
##for key, value in vixResults:
##    print(key + "    :" + str(value))
