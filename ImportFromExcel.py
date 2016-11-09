## To import excel file

import xlrd
import os
from operator import itemgetter
def importExcelVol():
    scriptpath = os.path.dirname(__file__) # 
    wb = xlrd.open_workbook(scriptpath + '/' + 'VIX_Calc_Example_CBOE_WhitePaper.xlsx')
    #sheet_names = wb.sheet_names()
    #print('Sheet Names', sheet_names)
    # NearExpiry
    sheet = wb.sheet_by_name('Python_Near')
    nearExpiryListSorted = list()
    for i in range(1,187):
        nearExpiryListSorted.append(sheet.row_values(i))
    # FarExpiry
    sheet = wb.sheet_by_name('Python_Far')
    farExpiryListSorted = list()
    for i in range(1,129):
        farExpiryListSorted.append(sheet.row_values(i))
    return nearExpiryListSorted, farExpiryListSorted
