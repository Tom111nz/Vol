#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 20:48:01 2018

@author: tomobrien
"""

""" next steps: more work on ratio. Use ratio to close position. Close and re-open position on same day ?
"""

from GetDeltaThroughTime import getDeltaThroughTime
from theDataEngine import theDataEngine
import matplotlib.pyplot as plt
import numpy as np
import datetime
from matplotlib.backends.backend_pdf import PdfPages

now = datetime.datetime.now()

expiryDetails = (
('F (Jan 18)','2018-01-17','2018-02-16'),
('G (Feb 18)','2018-02-14','2018-03-16'),
('H (Mar 18)','2018-03-21','2018-04-20'),
('J (Apr 18)','2018-04-18','2018-05-18'),
('K (May 18)','2018-05-16','2018-06-15'),
('M (Jun 18)','2018-06-20','2018-07-20'),
('N (Jul 18)','2018-07-18','2018-08-17'),
('Q (Aug 18)','2018-08-22','2018-09-21'),
('U (Sep 18)','2018-09-19','2018-10-19'),
('V (Oct 18)','2018-10-17','2018-11-16'))

deltaTargetList = [0.7]

#for row in expiryDetails:
#    getDeltaThroughTime(row[2] + ' 08:30:00', 0.7, 'p', True)

dKey, deltaDict = theDataEngine(deltaTargetList, expiryDetails)
# to retrieve output: deltaDict[0.7]['F (Jan 18)']['2018-02-15'][dKey['calculatedVIX']]
for delta in deltaTargetList:
    pp = PdfPages('StrategyCheck_' + str(now.strftime("%Y-%m-%d")) + '_' + str(delta) + '.pdf') 
    for futuresName in [row[0] for row in expiryDetails]:
        aDict = deltaDict[delta][futuresName]
        calculatedVix = list()
        vixFuture = list()
        bid = list()
        days = list()
        daysDatetime = list()
        ratioCalc = list()
        sqrtTTE = list()
        bidRatioed = list()
        for ct, day in enumerate(sorted(deltaDict[delta][futuresName].keys())):
            if aDict[day][dKey['calculatedVIX']] > 0.0:
                ratio = (aDict[day][dKey['bid']] / aDict[day][dKey['calculatedVIX']]) / aDict[day][dKey['sqrtTTE']]
            else:
                ratio = 1.0
            ratioCalc.append(ratio)
            calculatedVix.append(aDict[day][dKey['calculatedVIX']])
            vixFuture.append(aDict[day][dKey['VIX Future settle']])
            bid.append(aDict[day][dKey['bid']])
            sqrtTTE.append(aDict[day][dKey['sqrtTTE']])
            bidRatioed.append(bid[-1]/(ratioCalc[0]*sqrtTTE[-1]))
            days.append(day)
            daysDatetime.append(datetime.datetime.strptime(day, "%Y-%m-%d"))
        # calculate the ratio
        fig = plt.figure() # in inches!
        plt.rc('figure', figsize=(12, 8))
        ax = fig.add_subplot(111) 
        xAxis = range(len(calculatedVix))
        ax.plot(daysDatetime, calculatedVix, 'r-', daysDatetime, vixFuture, 'g-', daysDatetime, bidRatioed, 'r--', daysDatetime, bid, 'k--')
        #print(days[0][:7])
        #print(days[-1][:7])
        datemin = np.datetime64(days[0][:7], 'D')
        datemax = np.datetime64(days[-1][:7], 'D') + np.timedelta64(25, 'D')
        ax.set_xlim(datemin, datemax)
        #axes = fig.gca()
#        axes.set_ylim([0,min(300, max(calculatedVix)+20, max(bid)+20)])
#        ax2 = ax.twinx()
#        ax2.plot(daysDatetime, impliedVixFuture, 'r--')#, strikeXD, 'r--')
        ax.legend(['Calculated VIX', 'VIX Future', '30d Put bid (ratio-ed)', '30d Put bid (raw)'], loc='best')
        #ax2.legend(['Underlying', 'Strike'], loc=3)
        plt.title(futuresName)
        plt.grid()
        plt.show()
        if fig is not None:
            pp.savefig(fig)
            plt.close()
    pp.close()