import os
from ftplib import FTP
import zipfile
import io
import os
import csv
import sys
import time
import MySQLdb as mdb
import datetime
from LoadCBOEoptions import insertVolData
directory = 'ftp.datashop.livevol.com'
userName = 'amandatomnz@gmail.com'
password = 'eaw12345'

ftp = FTP(directory)   # connect to host, default port

ftp.login(user=userName, passwd=password)
##ftp.cwd("/order_609/UnderlyingOptionsEODCalcs/") # navigate to the directory for historical data
ftp.cwd("subscriptions/order_000003058/item_000004473/") # annual subscription
ftp.set_pasv(False)
listOfZipFiles = ftp.nlst()

con = mdb.connect(host="localhost",user="root",
                  passwd="password", db="Vol")
cur = con.cursor()

def gettext(ftp, filename, outfile=None):
    # fetch a text file
    # use a lambda to add newlines to the lines read from the server
    ftp.retrlines("RETR " + filename, lambda s, w=outfile.write: w(s+"\n"))

def getbinary(ftp, filename, outfile=None):
    # fetch a binary file
    try:
        ftp.retrbinary("RETR " + filename, outfile.write)
    except Exception as e:
        print("Running FTP exception ...")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]      
        print(exc_type, fname, exc_tb.tb_lineno)
        print("Try agin ...")
        ftp.retrbinary("RETR " + filename, outfile.write)

scriptpath = os.path.dirname('/Users/tomobrien/Documents/python/') #__file__
fileDirectory = scriptpath + "/CBOE_History/"
## get latest date in database
lastDateInDbQuery = "select substring(max(quote_date), 1, 10) from optionexpiry"
cur = con.cursor()
cur.execute(lastDateInDbQuery)
lastDateInDb = cur.fetchone();
cur.close()
print("Last Date in Db: " + lastDateInDb[0])

for zipfilename in sorted(listOfZipFiles): # Loop - looking for matching files
    try:
        datetime.datetime.strptime(zipfilename[-14:-4], "%Y-%m-%d")
    except:
        print("Problem datetime: " + str(zipfilename[-14:-4]))
        continue
    if datetime.datetime.strptime(zipfilename[-14:-4], "%Y-%m-%d") <= datetime.datetime.strptime(lastDateInDb[0], "%Y-%m-%d"):
        ##print("Not processing :" + zipfilename[-14:-4])
        continue
    start_time = time.time()
    zipfileDirectoryWithFileName = scriptpath + "/CBOE_History/" + zipfilename
    getbinary(ftp, zipfilename, open(os.path.expanduser(zipfileDirectoryWithFileName), 'wb'))
    try:
        zip_ref = zipfile.ZipFile(zipfileDirectoryWithFileName, 'r')
        zip_ref.extractall(fileDirectory)
        zip_ref.close()
    except (zipfile.BadZipfile):
        print(zipfileDirectoryWithFileName + " could not be opened; something wrong.")
        break
    csvFileDirectoryWithFileName = scriptpath + "/CBOE_History/" + zipfilename.replace(".zip", ".csv")
    insertVolData(csvFileDirectoryWithFileName, con)
    print("--- '%s' seconds for '%s'---" % ((time.time() - start_time), zipfilename))
    ## To delete the zip and csv file
    os.remove(scriptpath + "/CBOE_History/" + zipfilename.replace(".zip", ".csv"))
    os.remove(scriptpath + "/CBOE_History/" + zipfilename)
    
ftp.quit()
cur.close()
con.close()
