## Return list of VIXFuture and the correposnding option the VIX Future expires into
def VIXFutureOptionExpiryList():
    # 'G (Feb 06)' only has one data point
    VIXFutureOptionExpiryList = (
    ('G (Feb 06)','2006-02-15','2006-03-18'), 
    ('H (Mar 06)','2006-03-22','2006-04-22'),
    ('J (Apr 06)','2006-04-19','2006-05-20'),
    ('K (May 06)','2006-05-17','2006-06-17'),
    ('M (Jun 06)','2006-06-21','2006-07-22'),
    ('N (Jul 06)','2006-07-19','2006-08-19'),
    ('Q (Aug 06)','2006-08-16','2006-09-16'),
    ('U (Sep 06)','2006-09-20','2006-10-21'),
    ('V (Oct 06)','2006-10-18','2006-11-18'),
    ('X (Nov 06)','2006-11-15','2006-12-16'),
    ('Z (Dec 06)','2006-12-20','2007-01-20'),
    ('F (Jan 07)','2007-01-17','2007-02-17'),
    ('G (Feb 07)','2007-02-14','2007-03-17'),
    ('H (Mar 07)','2007-03-21','2007-04-21'),
    ('J (Apr 07)','2007-04-18','2007-05-19'),
    ('K (May 07)','2007-05-16','2007-06-16'),
    ('M (Jun 07)','2007-06-20','2007-07-21'),
    ('N (Jul 07)','2007-07-18','2007-08-18'),
    ('Q (Aug 07)','2007-08-22','2007-09-22'),
    ('U (Sep 07)','2007-09-19','2007-10-20'),
    ('V (Oct 07)','2007-10-17','2007-11-17'),
    ('X (Nov 07)','2007-11-21','2007-12-22'),
    ('Z (Dec 07)','2007-12-19','2008-01-19'),
    ('F (Jan 08)','2008-01-16','2008-02-16'),
    ('G (Feb 08)','2008-02-19','2008-03-22'),
    ('H (Mar 08)','2008-03-19','2008-04-19'),
    ('J (Apr 08)','2008-04-16','2008-05-17'),
    ('K (May 08)','2008-05-21','2008-06-21'),
    ('M (Jun 08)','2008-06-18','2008-07-19'),
    ('N (Jul 08)','2008-07-16','2008-08-16'),
    ('Q (Aug 08)','2008-08-20','2008-09-20'),
    ('U (Sep 08)','2008-09-17','2008-10-18'),
    ('V (Oct 08)','2008-10-22','2008-11-22'),
    ('X (Nov 08)','2008-11-19','2008-12-20'),
    ('Z (Dec 08)','2008-12-17','2009-01-17'),
    ('F (Jan 09)','2009-01-21','2009-02-21'),
    ('G (Feb 09)','2009-02-18','2009-03-21'),
    ('H (Mar 09)','2009-03-18','2009-04-18'),
    ('J (Apr 09)','2009-04-15','2009-05-16'),
    ('K (May 09)','2009-05-20','2009-06-20'),
    ('M (Jun 09)','2009-06-17','2009-07-18'),
    ('N (Jul 09)','2009-07-22','2009-08-22'),
    ('Q (Aug 09)','2009-08-19','2009-09-19'),
    ('U (Sep 09)','2009-09-16','2009-10-17'),
    ('V (Oct 09)','2009-10-21','2009-11-21'),
    ('X (Nov 09)','2009-11-18','2009-12-19'),
    ('Z (Dec 09)','2009-12-16','2010-01-16'),
    ('F (Jan 10)','2010-01-20','2010-02-20'),
    ('G (Feb 10)','2010-02-17','2010-03-20'),
    ('H (Mar 10)','2010-03-17','2010-04-17'),
    ('J (Apr 10)','2010-04-21','2010-05-22'),
    ('K (May 10)','2010-05-19','2010-06-19'),
    ('M (Jun 10)','2010-06-16','2010-07-17'),
    ('N (Jul 10)','2010-07-21','2010-08-21'),
    ('Q (Aug 10)','2010-08-18','2010-09-18'),
    ('U (Sep 10)','2010-09-15','2010-10-16'),
    ('V (Oct 10)','2010-10-20','2010-11-20'),
    ('X (Nov 10)','2010-11-17','2010-12-18'),
    ('Z (Dec 10)','2010-12-22','2011-01-22'),
    ('F (Jan 11)','2011-01-19','2011-02-19'),
    ('G (Feb 11)','2011-02-16','2011-03-19'),
    ('H (Mar 11)','2011-03-16','2011-04-16'),
    ('J (Apr 11)','2011-04-20','2011-05-21'),
    ('K (May 11)','2011-05-18','2011-06-18'),
    ('M (Jun 11)','2011-06-15','2011-07-16'),
    ('N (Jul 11)','2011-07-20','2011-08-20'),
    ('Q (Aug 11)','2011-08-17','2011-09-17'),
    ('U (Sep 11)','2011-09-21','2011-10-22'),
    ('V (Oct 11)','2011-10-19','2011-11-19'),
    ('X (Nov 11)','2011-11-16','2011-12-17'),
    ('Z (Dec 11)','2011-12-21','2012-01-21'),
    ('F (Jan 12)','2012-01-18','2012-02-18'),
    ('G (Feb 12)','2012-02-15','2012-03-17'),
    ('H (Mar 12)','2012-03-21','2012-04-21'),
    ('J (Apr 12)','2012-04-18','2012-05-19'),
    ('K (May 12)','2012-05-16','2012-06-16'),
    ('M (Jun 12)','2012-06-20','2012-07-21'),
    ('N (Jul 12)','2012-07-18','2012-08-18'),
    ('Q (Aug 12)','2012-08-22','2012-09-22'),
    ('U (Sep 12)','2012-09-19','2012-10-20'),
    ('V (Oct 12)','2012-10-17','2012-11-17'),
    ('X (Nov 12)','2012-11-21','2012-12-22'),
    ('Z (Dec 12)','2012-12-19','2013-01-19'),
    ('F (Jan 13)','2013-01-16','2013-02-16'),
    ('G (Feb 13)','2013-02-13','2013-03-16'),
    ('H (Mar 13)','2013-03-20','2013-04-20'),
    ('J (Apr 13)','2013-04-17','2013-05-18'),
    ('K (May 13)','2013-05-22','2013-06-22'),
    ('M (Jun 13)','2013-06-19','2013-07-20'),
    ('N (Jul 13)','2013-07-17','2013-08-17'),
    ('Q (Aug 13)','2013-08-21','2013-09-21'),
    ('U (Sep 13)','2013-09-18','2013-10-19'),
    ('V (Oct 13)','2013-10-16','2013-11-16'),
    ('X (Nov 13)','2013-11-20','2013-12-21'),
    ('Z (Dec 13)','2013-12-18','2014-01-18'),
    ('F (Jan 14)','2014-01-22','2014-02-22'),
    ('G (Feb 14)','2014-02-19','2014-03-22'),
    ('H (Mar 14)','2014-03-18','2014-04-19'),
    ('J (Apr 14)','2014-04-16','2014-05-17'),
    ('K (May 14)','2014-05-21','2014-06-21'),
    ('M (Jun 14)','2014-06-18','2014-07-19'),
    ('N (Jul 14)','2014-07-16','2014-08-16'),
    ('Q (Aug 14)','2014-08-20','2014-09-20'),
    ('U (Sep 14)','2014-09-17','2014-10-18'),
    ('V (Oct 14)','2014-10-22','2014-11-22'),
    ('X (Nov 14)','2014-11-19','2014-12-20'),
    ('Z (Dec 14)','2014-12-17','2015-01-17'),
    ('F (Jan 15)','2015-01-21','2015-02-20'),
    ('G (Feb 15)','2015-02-18','2015-03-20'),
    ('H (Mar 15)','2015-03-18','2015-04-17'),
    ('J (Apr 15)','2015-04-15','2015-05-15'),
    ('K (May 15)','2015-05-20','2015-06-19'),
    ('M (Jun 15)','2015-06-17','2015-07-17'),
    ('N (Jul 15)','2015-07-22','2015-08-21'),
    ('Q (Aug 15)','2015-08-19','2015-09-18'),
    ('U (Sep 15)','2015-09-16','2015-10-16'),
    ('V (Oct 15)','2015-10-21','2015-11-20'),
    ('X (Nov 15)','2015-11-18','2015-12-19'),
    ('Z (Dec 15)','2015-12-16','2016-01-15'),
    ('F (Jan 16)','2016-01-20','2016-02-19'),
    ('G (Feb 16)','2016-02-17','2016-03-18'),
    ('H (Mar 16)','2016-03-16','2016-04-15'),
    ('J (Apr 16)','2016-04-20','2016-05-20'),
    ('K (May 16)','2016-05-18','2016-06-17'),
    ('M (Jun 16)','2016-06-15','2016-07-15'),
    ('N (Jul 16)','2016-07-20','2016-08-19'),
    ('Q (Aug 16)','2016-08-17','2016-09-16'),
    ('U (Sep 16)','2016-09-21','2016-10-21'),
    ('V (Oct 16)','2016-10-19','2016-11-18'),
    ('X (Nov 16)','2016-11-16','2016-12-16'),
    ('Z (Dec 16)','2016-12-21','2017-01-20'),
    ('F (Jan 17)','2017-01-18','2017-02-17'),
    ('G (Feb 17)','2017-02-15','2017-03-17'),
    ('H (Mar 17)','2017-03-22','2017-04-21'),
    ('J (Apr 17)','2017-04-19','2017-05-19'),
    ('K (May 17)','2017-05-17','2017-06-16'),
    ('M (Jun 17)','2017-06-21','2017-07-21'),
    ('N (Jul 17)','2017-07-19','2017-08-18'),
    ('Q (Aug 17)','2017-08-16','2017-09-15'),
    ('U (Sep 17)','2017-09-20','2017-10-20'),
    ('V (Oct 17)','2017-10-18','2017-11-17'),
    ('X (Nov 17)','2017-11-15','2017-12-15'),
    ('Z (Dec 17)','2017-12-20','2018-01-19'),
    ('F (Jan 18)','2018-01-17','2018-02-16'),
    ('G (Feb 18)','2018-02-14','2018-03-16'),
    ('H (Mar 18)','2018-03-21','2018-04-20'),
    ('J (Apr 18)','2018-04-18','2018-05-18'),
    ('K (May 18)','2018-05-16','2018-06-15'),
    ('M (Jun 18)','2018-06-20','2018-07-20'),
    ('N (Jul 18)','2018-07-18','2018-08-17'),
    ('Q (Aug 18)','2018-08-22','2018-09-21'),
   ## ('U (Sep 18)','2018-09-19','2018-10-20'),
   ## ('V (Oct 18)','2018-10-17','2018-11-17'),
    ('X (Nov 18)','2018-11-21','2018-12-21'),
    ('Z (Dec 18)','2018-12-19','2019-01-18'),
    ##('F (Jan 19)','2019-01-16','2019-02-16'),
    ('G (Feb 19)','2019-02-13','2019-03-15')
    )
    return VIXFutureOptionExpiryList
