-- Option data
select oe.quote_date, und.underlying_bid_1545 from OptionExpiry oe 
left join underlying und on oe.id = und.optionexpiryid 
where oe.root = "SPX" and oe.expiration = '2017-09-15 08:30:00' 
group by oe.quote_date order by oe.quote_date;