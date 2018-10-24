## To scrape daily US Treasury yields into db
import requests, datetime
from bs4 import BeautifulSoup
import pymysql as mdb

def controlforNA(aRow):
    if aRow.strip() == 'N/A':
        val =  None
    else:
        val = float(aRow)/100.0
    return val

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
            cur.execute('''INSERT into USTreasuryYields (quote_date, 1M, 2M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y)
                              values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                              (scrappedDate.strftime("%Y-%m-%d"), controlforNA(row[1]), controlforNA(row[2]), controlforNA(row[3]), controlforNA(row[4]), controlforNA(row[5]), controlforNA(row[6]), controlforNA(row[7]), controlforNA(row[8]), controlforNA(row[9]), controlforNA(row[10]), controlforNA(row[11]), controlforNA(row[12])))
            con.commit()
            cur.close()
        except (mdb.Error, mdb.Warning) as e:
            print(e)
            print("USTreasuryYields: Error inserting %s: ", scrappedDate.strftime("%Y-%m-%d"))