## Insert US Treasury data from website
## https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yieldAll
import xlrd
import os
import sys
import MySQLdb as mdb
import datetime
## Db
con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")
# Load data from excel
fileName = "US_Treasury_Yields.xlsx"
scriptpath = os.path.dirname(__file__) # 
wb = xlrd.open_workbook(scriptpath + '/' + fileName)
sheet = wb.sheet_by_name('Data')

def DivideBy100(num):
    #print("num:" + str(num))
    if num is None:
        print("Is None")
        return None
    elif isinstance(num, float):
        if num == 0:
            return 0
        else:
            return num / 100
    elif isinstance(num, int):
        if num == 0:
            return 0
        else:
            return num / 100
        return float(num) / 100
    elif isinstance(num, str):
        if num == '0' or num == '': #### need to deal with data type and return back a string to insert into db
            return None
        else:
            return float(num) / 100
    else:
        print("Error in DivideBy100")
        return 999

# read in data
USTData = list()
print("Number of rows of Data :" + str(sheet.nrows))
for i in range(2,sheet.nrows - 1):
    row = sheet.row_values(i)
##    print(str(i))
##    asd = DivideBy100(row[11])
##    print(str(asd) + " : " + str(row[11]))
##    continue
    #print(row)
    #year, day, month, hour, minute, second = xlrd.xldate_as_tuple(row[0], 0) # convert excel date into python date
    if isinstance(row[0], float):
        year, day, month, hour, minute, second = xlrd.xldate_as_tuple(row[0], 0)
        py_date = datetime.datetime(year, month, day, hour, minute, second)
    else:
        #year, month, day, hour, minute, second = xlrd.xldate_as_tuple(row[0], 0)
        py_date = datetime.datetime.strptime(row[0], "%m/%d/%y").date()
##    print(py_date)
##    continue
##    sys.exit(0)
##    print(str(year))
##    print(str(month))
##    print(str(day))
##    py_date = datetime.datetime(year, month, day, hour, minute, second)
##    print(py_date.strftime("%Y-%m-%d"))
##    continue
    #sys.exit(0)
    try:
        # check data is not in Db
        cur = con.cursor()
        cur.execute("SELECT * from USTreasuryYields where quote_date = ""'%s'""" % py_date.strftime("%Y-%m-%d"))
        #print("SELECT quote_date from USTreasuryYields where quote_date = ""'%s'""" % py_date.strftime("%Y-%m-%d"))
        #sys.exit(0)
        check = cur.fetchone()
        cur.close()
        #print("check :" + str(check))
        if check is None:
            #print("Inserting into USTreasuryYields: '%s'" % str(py_date.strftime("%Y-%m-%d")))
            cur = con.cursor()
            cur.execute('''INSERT into USTreasuryYields (quote_date, 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y)
                  values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                  (py_date.strftime("%Y-%m-%d"), DivideBy100(row[1]),
                   DivideBy100(row[2]), DivideBy100(row[3]), DivideBy100(row[4]), DivideBy100(row[5]), DivideBy100(row[6]),
                   DivideBy100(row[7]), DivideBy100(row[8]), DivideBy100(row[9]), DivideBy100(row[10]), DivideBy100(row[11])))
            con.commit()
            cur.close()
    except (MySQLdb.Error, MySQLdb.Warning) as e:
        print(e)
        print("1: Error for %s %s:", date, row[1])
print("Finished!")
