import numpy as np
import datetime
from scipy import stats as ss 
import pymysql
import time 
from InterpolateUSYield import interpolateUSYield
import pandas as pd
from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry
import sys
start_time = time.time()

#Black (1976) Options on futures
def d1(F, K, sigma, T):
    return (np.log(F/K) + (sigma**2 / 2) * T)/(sigma * np.sqrt(T))

def d2(d1, sigma, T):
    return (d1 - (sigma * np.sqrt(T)))

def Black76(oType,F, K, r, sigma, T):
    d_1 = d1(F, K, sigma, T)
    d_2 = d2(d_1, sigma, T)
    if oType.upper() == "C":
        theo = np.exp(-r * T) * (F * ss.norm.cdf(d_1) - K * ss.norm.cdf(d_2))
        delta = ss.norm.cdf(d_1)
    else:
        theo = np.exp(-r * T) * (K * ss.norm.cdf(-d_2) - F * ss.norm.cdf(-d_1))
        delta = ss.norm.cdf(d_1) - 1

    return theo, delta

#tester = Black76("P", 19, 19, 0.1, 0.28, 0.75)
#for row in tester:
#    print(row)
    
con = pymysql.connect(host="localhost",user="root",
                  passwd="password",db="Vol", port = 3307)
cur = con.cursor()
    
sqlQuery = ("select oe.root, oe.quote_date, oe.expiration, oe.root, st.strike, st.option_type, EoD.opn, EoD.high, EoD.low, EoD.clos, EoD.trade_volume, og.`bid_size_1545`, og.`bid_1545`, og.`ask_size_1545`, og.`ask_1545`, und.`underlying_bid_1545`, und.`underlying_ask_1545`, und.`implied_underlying_price_1545`, und.`active_underlying_price_1545`, og.`implied_volatility_1545`, og.`delta_1545`, og.`gamma_1545`, og.`theta_1545`, og.`vega_1545`, og.`rho_1545`, Eod.`bid_size_eod`, eod.`bid_eod`, eod.`ask_size_eod`, eod.`ask_eod`, und.`underlying_bid_eod`, und.`underlying_ask_eod`, eod.`vwap`, eod.`open_interest`, eod.`delivery_code` " 
"from optionexpiry oe "
" join optiongreeks og on og.optionexpiryID = oe.ID "
" join Underlying und on und.optionexpiryID = oe.ID "
" join strike st on st.ID = og.strikeid "
" join EoD on EoD.OptionExpiryID = oe.ID and EOD.strikeiD = st.ID "
"where oe.ID in "
"( "
"select ID from optionexpiry "
"where quote_date = '2017-03-27 15:45:00'"
"and `rootOriginal` not in ('VIX', 'BVZ', 'SPXW')"
")"
"order by expiration, strike, option_type")
cur.execute(sqlQuery)
optionDataRaw = cur.fetchall()

colHeaders = ['root', 'quote_date', 'expiration', 'root1', 'strike', 'option_type', 'EoD.opn', 'EoD.high', 'EoD.low', 'EoD.clos', 'EoD.trade_volume', 'bid_size_1545', 
              'bid_1545', 'ask_size_1545', 'ask_1545', 'underlying_bid_1545', 'underlying_ask_1545', 'implied_underlying_price_1545', 'active_underlying_price_1545', 
              'implied_volatility_1545', 'delta_1545', 'gamma_1545', 'theta_1545', 'vega_1545', 'rho_1545', 'bid_size_eod', 'bid_eod', 'ask_size_eod', 'ask_eod', 
              'underlying_bid_eod', 'underlying_ask_eod', 'vwap', 'open_interest', 'delivery_code']
dKey = {}
for j in range(0, len(colHeaders)): # create numbering key for use below
    dKey[colHeaders[j]] = j
output = list()
for row in optionDataRaw:
    T = (row[dKey['expiration']] - row[dKey['quote_date']]).days / 365
    r = interpolateUSYield(row[dKey['quote_date']], row[dKey['expiration']])
    F = row[dKey['implied_underlying_price_1545']] * (1 + r * T)
    iVolShock = 0.05
    bs_theo, bs_delta = Black76(row[dKey['option_type']],F, row[dKey['strike']], r, row[dKey['implied_volatility_1545']]+iVolShock, T)
#    print('T ' + str(T))
#    print('r ' + str(r))
#    print('F ' + str(F))
#    print('bs_theo ' + str(bs_theo))
#    print('bs_delta ' + str(bs_delta))
    output.append([row[dKey['expiration']], row[dKey['strike']], row[dKey['option_type']], r, T, F, row[dKey['bid_1545']], row[dKey['ask_1545']], 
                   row[dKey['implied_volatility_1545']]+iVolShock, (row[dKey['bid_1545']] + row[dKey['ask_1545']]) * 0.5, bs_delta, bs_theo])

labels = ['optionExpiration', 'strike', 'option_type', 'r', 'T', 'F', 'bid_1545', 'ask_1545', 'implied_volatility_1545', 'mid_quote', 'delta', 'theo']
df = pd.DataFrame(output, columns = labels)
#df['optionExpiration'] = pd.to_datetime(df['optionExpiration'])
#for row1 in df['optionExpiration']:
#    print(row1)
#sys.exit(0)


# prepare to create distinct optionExpirations
formattedOptionExpirations = df['optionExpiration'].dt.to_pydatetime()

quoteDateKey = optionDataRaw[0][1]
calculateVIXFromSingleExpiry_PrintResults = False
calculateVIXFromSingleExpiry_use30DaysToExpiry = False
for rowOE in np.unique(formattedOptionExpirations):
    #isolate strike for a given expiry
    dataCalc = df[['optionExpiration','strike', 'option_type', 'bid_1545', 'ask_1545', 'theo', 'implied_volatility_1545']].loc[df['optionExpiration'] == rowOE]
    #print(str(rowOE) + ' ' + str(30dPut))
    ########### Need to feed in datablock in same format as required, as last parameter, and that is used if present, otherwise use the sql query in the calculateVIXFromSingleExpiry function
    ########### Expiration, strike, option_type, bid_1545 (original), ask_1545 (original), (og.bid_1545 + og.ask_1545)/2 (new theo), implied_volatility_1545 (new)
    VIXCalculated = calculateVIXFromSingleExpiry(datetime.datetime.strftime(quoteDateKey,"%Y-%m-%d") , datetime.datetime.strftime(rowOE,"%Y-%m-%d %H:%M:%S"), interpolateUSYield(quoteDateKey, rowOE), 
                                                 calculateVIXFromSingleExpiry_PrintResults, calculateVIXFromSingleExpiry_use30DaysToExpiry, dataCalc.values.tolist())
    print(str(rowOE) + ' ' + str(VIXCalculated))
df.to_csv('Black76_' + datetime.datetime.strftime(row[dKey['quote_date']],"%Y-%m-%d") + '_' + str(iVolShock) + '.csv')
























