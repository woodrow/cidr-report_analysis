#! /usr/bin/env python

import datetime
import time
import urllib2
import re
import logging
import logging.handlers

import get_cidr_report_dates

def main(logger):
    fq_urls = []
    urls = get_cidr_report_dates.get_partial_rv_urls(datetime.date.today())
    index_url = ''
    index_body = ''
    for url in urls:
        if index_url != url[:url.rfind('/')+1]:
#            if index_url != '':     #
#                return fq_urls      #
            index_url = url[:url.rfind('/')+1]
            try:
                time.sleep(1.0)
                req = urllib2.Request(index_url, data=None, headers={ 'User-agent': ("Mozilla/5.0 (compatible; ptolemy/0.1; "
                        "+http://ptolemy.csail.mit.edu")})
                response = urllib2.urlopen(req)
            except urllib2.URLError, e:
                logger.error(index_url + ": " + str(e))
                continue

            if response is not None:
                index_body = ''.join(response)
            else:
                index_body = ''

        re_url = url[url.rfind('/')+1:].replace('HHMM', r'\d\d\d\d')
        re_result = re.search('(' + re_url + ')', index_body)
        if re_result is not None:
            fq_urls.append(index_url + re_result.groups()[0])
        else:
            logger.error(
                "Couldn't fully qualify '{0}' [len(index_body) = {1}]".format(
                    url, len(index_body)))

    return fq_urls

if __name__ == '__main__':
    import pprint

    spider_logger = logging.getLogger()
    spider_logger.setLevel(logging.INFO)
    log_handler = logging.handlers.RotatingFileHandler(
        filename='qualifier_log', mode='a', maxBytes=2**20)
    log_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))
    spider_logger.addHandler(log_handler)

    fq_urls = main(spider_logger)
    f = open('rib_urls.txt', 'w')
    for url in fq_urls:
        f.write(url + '\n')
    f.close()
