## To scrape daily US Treasury yields into db
import requests, datetime
from bs4 import BeautifulSoup
import pymysql as mdb
con = mdb.connect(host="localhost",user="root",
                  passwd="password",db="Vol", port = 3307)
page = requests.get("https://www.treasury.gov/resource-center/data-chart-center/interest-rates/Pages/TextView.aspx?data=yield")
print('status code: ' + str(page.status_code)) # should be 200
soup = BeautifulSoup(page.content, 'html.parser')

# loop through even and odd rows
gridCellsEven = soup.find_all('tr', class_="evenrow")
gridCellsOdd = soup.find_all('tr', class_="oddrow")

newList = list()
for c in gridCellsEven:
    longString = c.get_text(" ")
    aList = longString.split(" ")
    newList.append(aList)
for c in gridCellsOdd:
    longString = c.get_text(" ")
    aList = longString.split(" ")
    newList.append(aList)

newListSorted = sorted(newList,key=lambda x: x[0]) # sort by date (first column)

# Retrieve latest date from database
sqlLatest = ('select max(quote_date) from USTreasuryYields')
cur = con.cursor()
cur.execute(sqlLatest)
latestDate = cur.fetchone()
cur.close()

latestDateInDb = datetime.datetime.combine(latestDate[0], datetime.datetime.min.time())
for row in newListSorted:
    scrappedDate = datetime.datetime.strptime(row[0], '%m/%d/%y')
    if scrappedDate > latestDateInDb: # compare datetimes and only insert larger dates
        try:
            print('INSERT into USTreasuryYields ' + scrappedDate.strftime("%Y-%m-%d"))
            cur = con.cursor()
            cur.execute('''INSERT into USTreasuryYields (quote_date, 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y)
                              values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                              (scrappedDate.strftime("%Y-%m-%d"), float(row[1])/100.0, float(row[2])/100.0, float(row[3])/100.0, float(row[4])/100.0, float(row[5])/100.0, float(row[6])/100.0, float(row[7])/100.0, float(row[8])/100.0, float(row[9])/100.0, float(row[10])/100.0, float(row[11])/100.0))
            con.commit()
            cur.close()
        except (mdb.Error, mdb.Warning) as e:
            print(e)
            print("USTreasuryYields: Error inserting %s: ", scrappedDate.strftime("%Y-%m-%d"))