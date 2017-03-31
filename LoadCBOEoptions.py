## Load in CBOE option data

from __future__ import print_function
from datetime import date, datetime, timedelta
import csv
import requests
import _mysql
import MySQLdb as mdb
from dateutil.parser import parse
import workdays
import datetime
import dateutil
import os
import time

def isDouble(val):
    try:
        val = float(val)
        return val
    except ValueError:
        return 0.0

##start_time = time.time()

##con = mdb.connect(host="localhost",user="root",
##                  passwd="password",db="Vol")
##cur = con.cursor()

##fileToOpen = r"~/Documents/python/^SPX-options-eod-calcs-20160426.csv"

##with open(os.path.expanduser(fileToOpen)) as f:
def insertVolData(csvFileDirectoryWithFileName, con):
    #print(time.time())
    #print(start_time)
    ##print("--- '%s' seconds to start insertVolData" % (time.time() - start_time))
    with open(csvFileDirectoryWithFileName) as f:
        reader = csv.reader(f, delimiter=',')
        next(reader, None) # skip first line because it is the column headers
        for row in reader:
            underlying_symbol = row[0]
            quote_dateTemp = row[1]
            quote_date = quote_dateTemp + " 15:45:00" # the datetime for greeks
            rootOriginal = row[2]
            expirationTemp = row[3]
            if rootOriginal == "SPX":
                expiration = expirationTemp + " 08:30:00"
                root = "SPX"
            elif rootOriginal == "SPXW":
                expiration = expirationTemp + " 15:00:00"
                root = "SPXW"
            elif rootOriginal == "VIX" or underlying_symbol == "^VIX":
                expiration = expirationTemp + " 08:30:00"
                root = "VIX"
            else:
                ##print("Root not recognized '%s': assigned to SPX" % rootOriginal)
                expiration = expirationTemp + " 08:30:00"
                root = "SPX"
            strike = row[4]
            option_type = row[5]
            opn = row[6]
            high = row[7]
            low = row[8]
            clos = row[9]
            trade_volume = row[10]
            bid_size_1545 = row[11]
            bid_1545 = row[12]
            ask_size_1545 = row[13]
            ask_1545 = row[14]
            underlying_bid_1545 = row[15]
            underlying_ask_1545 = row[16]
            implied_underlying_price_1545 = row[17]
            active_underlying_price_1545 = row[18]
            implied_volatility_1545 = row[19]
            delta_1545 = isDouble(row[20])
            gamma_1545 = isDouble(row[21])
            theta_1545 = isDouble(row[22])
            vega_1545 = isDouble(row[23])
            rho_1545 = isDouble(row[24])
            bid_size_eod = row[25]
            bid_eod = row[26]
            ask_size_eod = row[27]
            ask_eod = row[28]
            underlying_bid_eod = row[29]
            underlying_ask_eod = row[30]
            vwap = isDouble(row[31])
            open_interest = row[32]
            delivery_codeRaw = row[33]
            if delivery_codeRaw == '':
                delivery_code = 0
            else:
                delivery_code = delivery_codeRaw.replace("$", "")
            
            ## calendar time to expiry
            expirationDateTime = datetime.datetime.strptime(expiration, "%Y-%m-%d %H:%M:%S")
            quote_dateDateTime = datetime.datetime.strptime(quote_date, "%Y-%m-%d %H:%M:%S")
            calendarTTE = max(((expirationDateTime - quote_dateDateTime).total_seconds())/(60*60*24*365), 0) # 365 days/year
            ##print("Calendar '%s': Expiration: '%s' Quote_Date '%s': Seconds '%s'" % (calendarTTE, expirationDateTime, quote_dateDateTime, (expirationDateTime - quote_dateDateTime).total_seconds()))
            ##print("--- '%s' seconds to prepare data" % (time.time() - start_time))
            ##### OptionExpiry Table
            ## Check whether there is an entry in the OptionExpiry Table
            OptionExpiryQuery = "Select ID, root, rootOriginal from OptionExpiry where quote_date = '%s' and root = '%s' and expiration = '%s'" % (quote_date, root, expiration)
            cur = con.cursor()
            cur.execute(OptionExpiryQuery)
            OptionExpiryQueryResult = cur.fetchone();
            cur.close()
            if OptionExpiryQueryResult is None:
                try:
                    cur = con.cursor()
                    cur.execute('''Insert into OptionExpiry (quote_date, root, expiration, rootOriginal, calendarTTE) Values (%s, %s, %s, %s, %s)''',
                    (parse(quote_date).strftime("%Y-%m-%d %H:%M:%S"), root, parse(expiration).strftime("%Y-%m-%d %H:%M:%S"), rootOriginal, calendarTTE))
                    cur.close()
                    con.commit()
                except (mdb.Error, mdb.Warning) as e:
                    print(e)
                    print("1: Error for inserting into OptionExpiry: %s %s %s %s: Rolling Back" % (quote_date, root, rootOriginal, expiration))
                    # Rollback in case there is any error
                    db.rollback()
                    break
##            elif ((OptionExpiryQueryResult[1] == 'SPX' and OptionExpiryQueryResult[2] == 'SPX' and root == 'SPX' and rootOriginal == 'SPX') or
##                  (OptionExpiryQueryResult[1] == 'SPXW' and OptionExpiryQueryResult[2] == 'SPXW' and root == 'SPXW' and rootOriginal == 'SPXW')):
##                print("This file has been loaded already: '%s': exiting function" % (csvFileDirectoryWithFileName))
##                return ## exit the loop
##            else:
##                continue ## go to start of this loop
                ## recover the OptionExpiryID
                cur = con.cursor()
                cur.execute(OptionExpiryQuery)
                OptionExpiryIDTemp = cur.fetchone();
                OptionExpiryID = OptionExpiryIDTemp[0]
                cur.close()
            else:
                OptionExpiryID = OptionExpiryQueryResult[0]                   
            ##print("--- '%s' seconds to obtain optionExpiryID" % (time.time() - start_time))
            ##### Strike Table
            StrikeQuery = "Select ID from Strike where strike = '%s' and option_type = '%s'" % (strike, option_type)
            cur = con.cursor()
            cur.execute(StrikeQuery)
            StrikeQueryResult = cur.fetchone();
            cur.close()
            if StrikeQueryResult is None:
                try:
                    cur = con.cursor()
                    cur.execute('''Insert into Strike (strike, option_type) Values (%s, %s)''',
                    (strike, option_type))
                    cur.close()
                    con.commit()
                except (mdb.Error, mdb.Warning) as e:
                    print(e)
                    print("1: Error for inserting into Strike: %s %s: Rolling Back" % (strike, option_type))
                    # Rollback in case there is any error
                    db.rollback()
                    break
                ## recover the StrikeID
                cur = con.cursor()
                cur.execute(StrikeQuery)
                StrikeIDTemp = cur.fetchone();
                StrikeID = StrikeIDTemp[0]
                cur.close()
            else:
                StrikeID = StrikeQueryResult[0]
            ##print("--- '%s' seconds to obtain StrikeID" % (time.time() - start_time))
            ##### Underlying Table
            UnderlyingQuery = "Select ID from Underlying where OptionExpiryID = '%s'" % OptionExpiryID
            cur = con.cursor()
            cur.execute(UnderlyingQuery)
            UnderlyingID = cur.fetchone();
            cur.close()
            if UnderlyingID is None:
                try:
                    cur = con.cursor()
                    cur.execute('''Insert into Underlying (OptionExpiryID, underlying_bid_1545, underlying_ask_1545, implied_underlying_price_1545, active_underlying_price_1545, underlying_bid_eod, underlying_ask_eod) Values (%s, %s, %s, %s, %s, %s, %s)''',
                    (OptionExpiryID, underlying_bid_1545, underlying_ask_1545, implied_underlying_price_1545, active_underlying_price_1545, underlying_bid_eod, underlying_ask_eod))
                    cur.close()
                    con.commit()
                except (mdb.Error, mdb.Warning) as e:
                    print(e)
                    print("1: Error for inserting into Underlying: %s %s: Rolling Back" % (OptionExpiryID, underlying_bid_1545))
                    # Rollback in case there is any error
                    db.rollback()
                    break
            ##print("--- '%s' seconds to obtain UnderlyingID" % (time.time() - start_time))
            ##### OptionGreeks Table
            OptionGreeksQuery = "Select ID from OptionGreeks where OptionExpiryID = '%s' and StrikeID = '%s'" % (OptionExpiryID, StrikeID)
            cur = con.cursor()
            cur.execute(OptionGreeksQuery)
            OptionGreeksID = cur.fetchone();
            cur.close()
            if OptionGreeksID is None:
                try:
                    cur = con.cursor()
                    cur.execute('''Insert into OptionGreeks (OptionExpiryID, StrikeID, bid_size_1545, bid_1545, ask_size_1545, ask_1545, implied_volatility_1545, delta_1545, gamma_1545, theta_1545, vega_1545, rho_1545) Values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (OptionExpiryID, StrikeID, bid_size_1545, bid_1545, ask_size_1545, ask_1545, implied_volatility_1545, delta_1545, gamma_1545, theta_1545, vega_1545, rho_1545))
                    cur.close()
                    con.commit()
                except (mdb.Error, mdb.Warning) as e:
                    print(e)
                    print("1: Error for inserting into OptionGreeks: %s %s %s: Rolling Back" % (OptionExpiryID, StrikeID, bid_size_1545))
                    # Rollback in case there is any error
                    db.rollback()
                    break
            ##print("--- '%s' seconds to insert OptionGreeks" % (time.time() - start_time))
            ##### EoD Table
            EoDQuery = "Select ID from EoD where OptionExpiryID = '%s' and StrikeID = '%s'" % (OptionExpiryID, StrikeID)
            cur = con.cursor()
            cur.execute(EoDQuery)
            EoDID = cur.fetchone();
            cur.close()
            if EoDID is None:
                try:
                    cur = con.cursor()
                    cur.execute('''Insert into EoD (OptionExpiryID, StrikeID, opn, high, low, clos, trade_volume, bid_size_eod, bid_eod, ask_size_eod, ask_eod, vwap, open_interest, delivery_code) Values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (OptionExpiryID, StrikeID, opn, high, low, clos, trade_volume, bid_size_eod, bid_eod, ask_size_eod, ask_eod, vwap, open_interest, delivery_code))
                    cur.close()
                    con.commit()
                except (mdb.Error, mdb.Warning) as e:
                    print(e)
                    print("1: Error for inserting into EoD: %s %s %s: Rolling Back" % (OptionExpiryID, StrikeID, bid_size_1545))
                    # Rollback in case there is any error
                    db.rollback()
                    break
            ##print("--- '%s' seconds to insert EoD" % (time.time() - start_time))
##print("--- '%s' seconds ---" % (time.time() - start_time))
