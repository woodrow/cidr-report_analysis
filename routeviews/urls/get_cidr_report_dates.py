#! /usr/bin/env python

import datetime

"""Returns a list of dates on which the CIDR report has likely been published,
up to the specified end_date.

"""
def get_cidr_report_dates(end_date):
    dates = []
    # 1997-11-14 is the first CIDR report day with Route Views data
    d = datetime.date(1997, 11, 14)
    while(d < end_date):
        dates.append(d)
        d = datetime.date.fromordinal(d.toordinal() + 7)
    return dates

"""Returns a list of URLs representing Route Views RIB dumps for the same day
that the CIDR report is released, up to the specified end_date. The URLs
contain the string 'HHMM' which must be replaced by the lowest
(i.e. closest to midnight) time available on the index
(i.e. url[:url.rfind('/')]).

"""
def get_partial_rv_urls(end_date):
    urls = []
    for d in get_cidr_report_dates(end_date):
        if d <= datetime.date(1999, 12, 31):
            urls.append(d.strftime("http://archive.routeviews.org/"
                "oix-route-views/%Y.%m/oix-full-%Y-%m-%d-HHMM.dat.bz2"))
        elif d <= datetime.date(2001, 11, 01):
            urls.append(d.strftime("http://archive.routeviews.org/"
                "oix-route-views/%Y.%m/"
                "oix-full-snapshot-%Y-%m-%d-HHMM.dat.bz2"))
        else:  # switch over to MRT-flavored RIB dumps
            urls.append(d.strftime("http://archive.routeviews.org/"
                "bgpdata/%Y.%m/RIBS/rib.%Y%m%d.HHMM.bz2"))
    return urls

if __name__ == '__main__':
    import pprint
    pprint.pprint(get_rv_cr_urls(datetime.date.today()))
