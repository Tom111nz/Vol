from calculateVIXFromSingleExpiry import calculateVIXFromSingleExpiry

quote_date = '2016-11-25' #'2017-07-25'
optionExpiration_date = '2017-09-15 08:30:00'
r = 0.01
output = calculateVIXFromSingleExpiry(quote_date, optionExpiration_date, r, False, False)
print(str(output))
