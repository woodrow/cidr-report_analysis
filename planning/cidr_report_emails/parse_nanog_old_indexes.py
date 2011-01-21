#!/usr/bin/env python2.6

import re
import sys
import os
import datetime

def parse_file(filename):
    output = []
    f = open(os.path.realpath(filename))
    for line in f:
        match = re.search('<LI>(\d{2}/\d{2}/\d{2})\s*'
            '<STRONG><a.*?href=\"(.*?)\".*?>(.*?)</a>.*?<EM>(.*?)</EM>',line)
        if match:
            (date, url, subject, author) = match.groups()
            dateparts = [int(x) for x in date.split('/')]
            if dateparts[2] > 10:
                dateparts[2] += 1900
            else:
                dateparts[2] += 2000
            date = datetime.date(dateparts[2], dateparts[0], dateparts[1])
            url = ('http://www.merit.edu/mail.archives/nanog/'
                '{0}-{1:02}/{2}').format(date.year, date.month, url)
            output.append((date, subject, author, url))
    f.close()
    return output

if __name__ == '__main__':
    if len(sys.argv) > 1:
        output = []
        for filename in sys.argv[1:]:
            output += parse_file(filename)
        output.sort(key=lambda x: x[0], reverse=True)
        for t in output:
            print('{0}\t{1}\t{2}\t{3}'.format(
                t[0].isoformat(), t[1], t[2], t[3]))
    else:
        print("USAGE: list of filenames of old-style nanog archive index "
             "files to process")