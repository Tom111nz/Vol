select oe.root, oe.quote_date, oe.expiration, oe.root, st.strike, st.option_type, EoD.opn, EoD.high, EoD.low, EoD.clos, EoD.trade_volume, og.`bid_size_1545`, og.`bid_1545`, og.`ask_size_1545`, og.`ask_1545`, und.`underlying_bid_1545`, und.`underlying_ask_1545`, und.`implied_underlying_price_1545`, und.`active_underlying_price_1545`, og.`implied_volatility_1545`, og.`delta_1545`, og.`gamma_1545`, og.`theta_1545`, og.`vega_1545`, og.`rho_1545`, Eod.`bid_size_eod`, eod.`bid_eod`, eod.`ask_size_eod`, eod.`ask_eod`, und.`underlying_bid_eod`, und.`underlying_ask_eod`, eod.`vwap`, eod.`open_interest`, eod.`delivery_code` 
from optionexpiry oe
 join optiongreeks og on og.optionexpiryID = oe.ID
 join Underlying und on und.optionexpiryID = oe.ID
 join strike st on st.ID = og.strikeid
 join EoD on EoD.OptionExpiryID = oe.ID and EOD.strikeiD = st.ID
where oe.ID in 
(
select * from optionexpiry 
where quote_date = '2017-03-27 15:45:00'
and `rootOriginal` not in ('VIX', 'BVZ')
)
##and oe.root not in ('VIX', 'BVZ')
##group by oe.root, oe.quote_date, oe.expiration
order by expiration, strike

##--oe.root, st.strike, st.option_type, EoD.opn, EoD.high, EoD.low, EoD.clos, EoD.trade_volume, Eod.`bid_size_eod`, eod.`bid_eod` 