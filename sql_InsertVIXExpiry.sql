select * from vixfuturesexpiry
where ExpiryDate = '2019-03-19';

insert into vixfuturesexpiry (Contract, ExpiryDate)
values ('J (Apr 20)', '2020-04-15');


--update vixfuturesexpiry
--set Contract = 'H (Mar 19)'
--where ExpiryDate = '2019-03-19'

