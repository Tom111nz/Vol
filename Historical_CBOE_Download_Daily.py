## Insert daily option files one at a time
import MySQLdb as mdb
import os
from ftplib import FTP
import zipfile
import sys
from LoadCBOEoptions import insertVolData
from Historical_CBOE_Download import getbinary

## enter new file name here
zipfilename = 'UnderlyingOptionsEODCalcs_2017-08-21.zip' 
##

directory = 'ftp.datashop.livevol.com'
userName = 'amandatomnz@gmail.com'
password = 'eaw12345'

ftp = FTP(directory)   # connect to host, default port

ftp.login(user=userName, passwd=password)
##ftp.cwd("/order_609/UnderlyingOptionsEODCalcs/") # navigate to the directory for historical data
ftp.cwd("subscriptions/UnderlyingOptionsEODCalcs_OneYearSubscription/") # annual subscription
ftp.set_pasv(False)

con = mdb.connect(host="localhost",user="root",
                  passwd="password", db="Vol")
scriptpath = os.path.dirname('/Users/tomobrien/Documents/python/')
fileDirectory = scriptpath + "/CBOE_History/"
zipfileDirectoryWithFileName = scriptpath + "/CBOE_History/" + zipfilename
getbinary(ftp, zipfilename, open(os.path.expanduser(zipfileDirectoryWithFileName), 'wb'))
try:
    zip_ref = zipfile.ZipFile(zipfileDirectoryWithFileName, 'r')
    zip_ref.extractall(fileDirectory)
    zip_ref.close()
except (zipfile.BadZipfile):
    print(zipfileDirectoryWithFileName + " could not be opened; something wrong.")
    sys.exit()

csvFileDirectoryWithFileName = scriptpath + "/CBOE_History/" + zipfilename.replace(".zip", ".csv")
insertVolData(csvFileDirectoryWithFileName, con)
ftp.quit()
con.close()
