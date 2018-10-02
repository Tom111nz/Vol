import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import math
import numpy as np
from scipy import stats as ss 
import datetime
import calendar
import sys
import matplotlib.pyplot as plt
#Black Schole Options on x
def d1(S, K, sigma, T, r, rf):
    return (np.log(S/K) + (r - rf + sigma**2 / 2) * T)/(sigma * np.sqrt(T))

def d2(d1, sigma, T):
    return (d1 - (sigma * np.sqrt(T)))

def BS_FX(oType, S, K, r, sigma, T, rf):
    d_1 = d1(S, K, sigma, T, r, rf)
    d_2 = d2(d_1, sigma, T)
    if oType.upper() == "C":
        theo = S * np.exp(-rf * T) * ss.norm.cdf(d_1) - K * np.exp(-r * T) * ss.norm.cdf(d_2)
        delta = np.exp(-rf * T) * ss.norm.cdf(d_1)
    else:
        theo = K * np.exp(-r * T) * ss.norm.cdf(-d_2) - S * np.exp(-rf * T) * ss.norm.cdf(-d_1)
        delta = np.exp(-rf * T) * ss.norm.cdf(d_1) - np.exp(-rf * T)
    gamma = ss.norm.pdf(d_1) * np.exp(-rf*T)/(S * sigma * math.sqrt(T))
    if np.isnan(gamma):
        gamma = 0
    return theo, delta, gamma

def logContract(S, K, sigma, T, r, rf):
    theo = math.exp(-r*T) * (math.log(S / K) + (r - sigma**2 / 2) * T)
    delta = math.exp(-r*T) / S
    return theo, delta
    
#theo, delta, gamma = BS_FX('C', 55, 60, 0.1, 0.3, 0.75, 0.1)
#theo, delta, gamma = BS_FX('C', 150, 152, 0.03, 0.13, 91/365, 0.04)
#print(theo)
#print(delta)
#print(gamma)
#sys.exit(0)
df = pd.read_excel('LogContractData.xlsx', sheetname='Sheet1')
#print(df)
year = 1987
month = 5
realisedVolList = list()
realisedVolFromLogContractList = list()
hedgeErrorList = list()
logHedgeErrorList = list()
for q in range(0, 60):
    month = month + 1
    if month > 12:
        month = 1
        year = year + 1
    mask = (df['Date'] >= datetime.datetime(year, month, 1)) & (df['Date'] <= datetime.datetime(year, month, calendar.monthrange(year, month)[1]))
    dfMonthly = df.loc[mask]
    dateList = dfMonthly['Date'].tolist()
    fxList = dfMonthly['PX_LAST'].tolist()
    sigma = 0.108
    oType = 'C'
    r = 0.0
    rf = 0.0
    K = fxList[0]   
    theoList = list()
    deltaList = list()
    gammaList = list()
    logTheoList = list()
    logDeltaList = list()
    for x in range(0, len(fxList)):
        theo, delta, gamma = BS_FX(oType, fxList[x], K, r, sigma, (dateList[-1] - dateList[x]).days/365, rf)
        theoList.append(theo)
        deltaList.append(delta)
        gammaList.append(gamma)
        logTheo, logDelta = logContract(fxList[x], K, r, sigma, (dateList[-1] - dateList[x]).days/365, rf)
        logTheoList.append(math.log(fxList[x]))
        logDeltaList.append(1/fxList[x])
    pnl = 0
    logPnl = 0
    logPnl2 = 0
    for x in range(1, len(fxList)):
        #pnl = pnl + deltaList[x-1] * (fxList[x] - fxList[x-1])
        pnl = pnl + gammaList[x] * math.pow(fxList[x], 2) * (math.pow(math.log(fxList[x]/fxList[x-1]), 2) - (sigma**2) * (1 / 252))
        logPnl2 = logPnl2 + logDeltaList[x-1] * (fxList[x] - fxList[x-1]) # long underlying
        logPnl = logPnl + 1 * (math.pow(math.log(fxList[x]/fxList[x-1]), 2) - (sigma**2) * (1 / 252))
    #payoff = theoList[0] - max(fxList[-1] -  K, 0)
    #pnl = pnl + payoff 
    logPayoff = -(logTheoList[-1] - logTheoList[0]) # short log future position
    logPnl2 = logPnl2 + logPayoff
    
    # realised vol
    fxListLogSquared = list()

    for x in range(1, len(fxList)):
        fxListLogSquared.append(math.pow(math.log(fxList[x]/fxList[x-1]), 2))
    realisedVol = math.sqrt(sum(fxListLogSquared) * (252 / (len(fxList)-1)))
    realisedVolFromLogContract = math.sqrt(2/((len(fxList)-1)/252) * logPnl2)
    # outputs
    print(year)
    print(month)
    print('theoList[0]: ' + str(theoList[0]))
    print('pnl: ' + str(pnl))
    print('logPnl: ' + str(logPnl))
    #print('logPayoff: ' + str(logPayoff))
    print((pnl / theoList[0]))
    print('realisedVol: ' + str(realisedVol))
    print('realisedVolFromLogContract: ' + str(realisedVolFromLogContract))
    print('len(fxList): ' + str(len(fxList)))
    realisedVolList.append(realisedVol)
    realisedVolFromLogContractList.append(realisedVolFromLogContract)
    hedgeErrorList.append((0.5 * -pnl / theoList[0]))
    logHedgeErrorList.append((1000 * 0.5 * -logPnl))

print('Average monthly realised vol: ' + str(np.mean(realisedVolList)))

herList = list()
for rv in realisedVolList:
    her = -41.3*rv**2 + 0.5
    herList.append(her)

# graph
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1, axisbg="1.0")
data = ((realisedVolList, hedgeErrorList), (realisedVolList, logHedgeErrorList),(realisedVolList, herList) )
colors = ("red", "green", "black")
groups = ("BS delta", "Log contract", "Check") 
for data, color, group in zip(data, colors, groups):
    x, y = data
    ax.scatter(x, y, alpha=0.8, c=color, edgecolors='none', s=30, label=group)
plt.title('Hedge error / option premium')
plt.legend()
plt.xlim([0.05, 0.2])
ax = fig.gca()
#ax.set_xticks(np.arange(0.05, 0.17, 0.01))
#ax.set_yticks(np.arange(-1.2, 1., 0.1))
plt.grid()
plt.show()

#print('realisedVolList')
#for row in realisedVolList:
#    print(row)
#print('realisedVolFromLogContractList')
#for row in realisedVolFromLogContractList:
#    print(row)
#for row in gammaList:
#    print(row)
#for row in hedgeErrorList:
#    print(row)






















