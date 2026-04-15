 SELECT
        CAST(vc.quote_date AS DATETIME) AS QuoteDate,
        vc.vixcalculated,
        vf.clos 'VixFutureClose',
        st.strike,
        st.option_type,
        og.bid_1545 as 'Theo_Bid',
        og.delta_1545 as 'Delta'
        FROM vixcalculated vc
        LEFT JOIN vixfutures vf
        ON vf.tradedate = vc.quote_date
        AND vf.contract = vc.futurescontract
        LEFT JOIN optiongreeks og
        ON og.optionexpiryId = vc.optionexpiryID
        LEFT JOIN strike st
        ON st.id = og.strikeiD
        WHERE vc.futurescontract LIKE '% (Feb 26)'
        AND vf.clos is not null
        and vf.clos <> 0.0
        and vc.quote_date > '2026-01-31'
        ORDER by vc.quote_date;
        


