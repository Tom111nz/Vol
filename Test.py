#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 20 20:42:15 2017

@author: tomobrien
"""


#import mysql-connector-python as mcp
#import socket
#s = socket.socket() #Create a socket object
#host = socket.gethostname() #Get the local machine name
#port = 3306 # Reserve a port for your service
#s.bind(('',port)) #Bind to the port
import mysql.connector
#import MySQLdb as mdb
#con = mdb.connect(host="localhost",user="root",
#                  passwd="password",db="Vol")
mysql.connector.connect(host='localhost',database='mysql',user='root',password='')
#con = mysql.connector.connect(user='root', password='password',
#                              host='localhost',
#                              database='Vols')
sqlQuery = ('select oe.quote_date, oe.Expiration, st.strike, st.option_type, og.delta_1545, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545, og.vega_1545 from optiongreeks og ' 
    'join optionexpiry oe on oe.ID = og.optionexpiryID '
    'join strike st on st.ID = og.strikeID '
    'where oe.ID in '
    '( '
    'select ID from optionexpiry where rootOriginal in ("SPX") and expiration = '"'2016-10-21 08:30:00'"' '
    ') '
    'and st.option_type = '"'c'"' '
    'order by oe.quote_date, oe.Expiration, st.strike;')

cur = con.cursor()
cur.execute(sqlQuery)
strikeDataRaw = cur.fetchall()
cur.close()

print(len(strikeDataRaw))