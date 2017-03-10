select * from VIXFutures 
                    where contract = 'G (Feb 09)'
                    order by TradeDate asc;
                    
select oe.quote_date, und.underlying_bid_1545 from OptionExpiry oe 
                    left join underlying und on oe.id = und.optionexpiryid 
                    where oe.root = "SPX" 
                    and oe.expiration = '2009-03-21 08:30:00'
                    group by oe.quote_date order by oe.quote_date;

select TradeDate, Settle from VIXFutures 
                    where contract = 'H (Mar 06)'
                    order by TradeDate asc;


select * from optionexpiry
where expiration = '2006-04-22 08:30:00'
and root = 'SPX';

select oe.quote_date, oe.Expiration, st.strike, st.option_type, og.delta_1545, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545, og.vega_1545, 
        case when st.option_type = "c" then abs(0.95 - delta_1545) else abs(0.95 - (1-abs(delta_1545))) end as "delta_gap" from optiongreeks og 
        join optionexpiry oe on oe.ID = og.optionexpiryID 
        join strike st on st.ID = og.strikeID 
        where oe.ID in 
        (
        21671##select ID from optionexpiry where root in ("SPX") and expiration = '2011-06-18 08:30:00' and quote_date = '2009-06-25 15:45:00'
        ) 
        ##and st.option_type = 'p'
        order by oe.quote_date, oe.Expiration, st.strike;

select * from optiongreeks where optionexpiryid = 13907
        
select oe.quote_date, und.underlying_bid_1545 from OptionExpiry oe 
                    left join underlying und on oe.id = und.optionexpiryid 
                    where oe.root = "SPX" 
                    and oe.expiration = '2006-04-22 08:30:00'
                    group by oe.quote_date order by oe.quote_date;
                    
select oe.Expiration, st.strike, st.option_type, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545 from optiongreeks og join optionexpiry oe on oe.ID = og.optionexpiryID join strike st on st.ID = og.strikeID where og.optionexpiryID = (select ID from optionexpiry where substring(quote_date, 1, 10) = '2005-06-21' and root in ("SPX") and expiration = '2006-06-17 08:30:00')order by oe.Expiration, st.strike;

select *from OptionExpiry oe 
                    left join underlying und on oe.id = und.optionexpiryid 
                    where oe.root = "SPX" 
                    and oe.expiration = '2009-03-21 08:30:00'
                    group by oe.quote_date order by oe.quote_date;
                    
select oe.Expiration, st.strike, st.option_type, og.bid_1545, og.ask_1545, (og.bid_1545 + og.ask_1545)/2, og.implied_volatility_1545 from optiongreeks og join optionexpiry oe on oe.ID = og.optionexpiryID join strike st on st.ID = og.strikeID where og.optionexpiryID = (select ID from optionexpiry where substring(quote_date, 1, 10) = '2009-06-25' and root in ("SPX") and expiration = '2011-06-18 08:30:00')order by oe.Expiration, st.strike;