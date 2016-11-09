from __future__ import print_function
from datetime import date, datetime, timedelta
import csv
import requests
import _mysql
import MySQLdb as mdb
from dateutil.parser import parse

VIXList = ['http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vixcurrent.csv']


con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol")

for v in VIXList:
    with requests.Session() as s:
        download = s.get(v)
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        print("Number of rows in csv file:" + str(my_list.__len__()))
        for row in my_list[2:]:
            date = row[0]
            if date and not date.isspace():
                # check date is not in database
                cur = con.cursor()
                isDateQuery = "Select TradeDate from VIX where TradeDate = '" + str(parse(date).strftime("%Y-%m-%d")) + "'"
                cur.execute(isDateQuery)
                if cur.fetchone() is None:
                    cur.execute('''INSERT into VIX (TradeDate, Opn, High, Low, Clos)
                          values (%s, %s, %s, %s, %s)''',
                          (parse(date).strftime("%Y-%m-%d %H:%M:%S"), row[1], row[2], row[3], row[4]))
                    cur.close()
                    con.commit()
                    print("Inserted into VIX:" +str(parse(date).strftime("%Y-%m-%d")))
                else:
                    cur.close()
            else:
                print("Skipped Date")
con.close()
