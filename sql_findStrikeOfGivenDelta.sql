select
tempi.*
from 
(
select oe.quote_date, oe.expiration, st.`option_type`, st.strike, delta_1545, 
case when st.option_type = 'c' then abs(0.75 - delta_1545) else abs(0.75 - (1-abs(delta_1545))) end as 'delta_gap', 
(og.bid_1545 + og.ask_1545)/2 as 'mid' from optiongreeks og
join optionexpiry oe on oe.id = og.optionexpiryid
join strike st on st.id = og.strikeid
where oe.id in (
select ID from optionexpiry 
where expiration =  '2007-05-19 08:30:00'
and rootoriginal = 'SPX'
)
and st.option_type = 'p'
) tempi
join
(
select oe.quote_date, 
min(case when st.option_type = 'c' then abs(0.75 - delta_1545) else abs(0.75 - (1-abs(delta_1545))) end) as 'min_delta_gap' 
from optiongreeks og
join optionexpiry oe on oe.id = og.optionexpiryid
join strike st on st.id = og.strikeid
where oe.id in (
select ID from optionexpiry 
where expiration =  '2007-05-19 08:30:00'
and rootoriginal = 'SPX'
)
and st.option_type = 'p'
group by oe.quote_date
) tempj on tempj.quote_date = tempi.quote_date and tempj.min_delta_gap = tempi.delta_gap
