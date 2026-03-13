import paramiko
import zipfile
import time
import pymysql as mdb
import datetime
from LoadCBOEoptionsNew import insertVolData
import os


def get_db_connection():
    try:
        return mdb.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            passwd=os.environ["DB_PASSWORD"],
            db=os.environ["DB_NAME"],
            port=int(os.environ.get("DB_PORT", "3306")),
            autocommit=False
        )
    except KeyError as e:
        raise RuntimeError(f"Missing required environment variable: {e}")

con = get_db_connection()
cur = con.cursor()

HOST = "sftp.datashop.livevol.com"
PORT = 22
USERNAME = "amandatomnz_gmail_com"
PASSWORD = "Eaws12345$"

REMOTE_DIR = "subscriptions/order_000016592/item_000020515"          # change if they give you a folder like "/outgoing"
#REMOTE_DIR = "order_000091865/item_000105087" # historical
LOCAL_DIR = r"C:\Temp\livevol"  # change to where you want files

os.makedirs(LOCAL_DIR, exist_ok=True)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Connect
ssh.connect(
    hostname=HOST,
    port=PORT,
    username=USERNAME,
    password=PASSWORD,
    timeout=20,
    banner_timeout=20,
    auth_timeout=20,
)

# Open SFTP session
sftp = ssh.open_sftp()

try:
    sftp.chdir(REMOTE_DIR)
except FileNotFoundError:
    print("Remote directory not found:", REMOTE_DIR)
    print("Top-level:", sftp.listdir("."))
    print("Under 'subscriptions':", sftp.listdir("subscriptions"))
    raise

# List files
listOfZipFiles = sftp.listdir(".")
print("Remote files:", listOfZipFiles)

scriptpath = r"C:\Temp"
fileDirectory = os.path.join(scriptpath, "CBOE_History")
os.makedirs(fileDirectory, exist_ok=True)

## get latest date in database
lastDateInDbQuery = "select coalesce(substring(max(quote_date), 1, 10), '1900-01-01') from optionexpiry"
cur.execute(lastDateInDbQuery)
lastDateInDb = cur.fetchone()
cur.close()
print("Last Date in Db: " + lastDateInDb[0])

for zipfilename in sorted(listOfZipFiles): # Loop - looking for matching files
     print(zipfilename)
     try:
         datetime.datetime.strptime(zipfilename[-14:-4], "%Y-%m-%d")
     except:
         print("Problem datetime: " + str(zipfilename[-14:-4]))
         continue
     if datetime.datetime.strptime(zipfilename[-14:-4], "%Y-%m-%d") <= datetime.datetime.strptime(lastDateInDb[0],
                                                                                                 "%Y-%m-%d"):
        print("Not processing :" + zipfilename[-14:-4])
        continue

     start_time = time.time()
     zipfileDirectoryWithFileName = os.path.join(fileDirectory, zipfilename)
     sftp.get(zipfilename, zipfileDirectoryWithFileName)
     try:
        zip_ref = zipfile.ZipFile(zipfileDirectoryWithFileName, 'r')
        zip_ref.extractall(fileDirectory)
        zip_ref.close()
     except (zipfile.BadZipfile):
        print(zipfileDirectoryWithFileName + " could not be opened; something wrong.")
        break
     csvFileDirectoryWithFileName = os.path.join(fileDirectory, zipfilename.replace(".zip", ".csv"))
     insertVolData(csvFileDirectoryWithFileName, con, 2000, False)
     print("--- %s seconds for %s---" % (round((time.time() - start_time), 0), zipfilename))
     ## To delete the zip and csv file
     os.remove(csvFileDirectoryWithFileName)
     os.remove(zipfileDirectoryWithFileName)

sftp.close()
ssh.close()
cur.close()
con.close()
