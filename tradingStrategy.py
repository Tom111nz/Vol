#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 23 19:18:57 2018

@author: tomobrien
"""
import pandas as pd
## trading strategy template
def tradingStrategy(deltaDict, dKey, delta, futuresName, futuresExpiry, optionExpiry):
    aDict = deltaDict[delta][futuresName]
    futuresDayList = list()
    sortedDays = sorted(aDict.keys())
    
    ### Turn the Dict ito panal data
    pd.DataFrame.from_dict(aDict, orient='index', columns=dKey)
    ### need to get this working with jupyter notebook
    
    
    
    
### The Vix Future
    for ct, day in enumerate(sortedDays): # start at second available date
        if aDict[day][dKey['VIX Future settle']] > 0.0:
            if ct == 0:
                pnl_futures = 0.0
            else:
                pnl_futures = 1000.0 * (aDict[day][dKey['VIX Future settle']] - aDict[sortedDays[u-1]][dKey['VIX Future settle']])
            

    ### Now loop through from the first date to the expiry date of the future
    