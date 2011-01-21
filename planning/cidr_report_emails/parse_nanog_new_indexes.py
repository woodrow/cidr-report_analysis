#!/usr/bin/env python2.6

import re
import sys
import os
import datetime

def parse_file(filename):
    output = []
    f = open(os.path.realpath(filename))
    grepblock = ''
    line_count = 0
    block_startline = 1
    for line in f:
        line_count += 1
        if re.match('(From .*? (?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) +' 
            '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) +'
            '\d{1,2} +\d{2}\:\d{2}\:\d{2} +\d{4})\n', line):
            if grepblock:
                # strip tabs
                grepblock = re.sub("\t", " ", grepblock)
    
                # group 1: date. group 2: sender name. group 3: subject
                matches = re.search('((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) +'
                    '(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) +'
                    '\d{1,2} +\d{2}\:\d{2}\:\d{2} +\d{4})\n'
                    '.*\(([^\)]*)\).*\n.*\nSubject: ([^\n]*)\n',
                    grepblock,flags=re.M|re.I)
                if matches:
                    groups = matches.groups()
                    
                    date = datetime.datetime.strptime(groups[0], 
                        '%a %b %d %H:%M:%S %Y')
                    subject = groups[2]
                    author = groups[1]
                    range_tuple = (block_startline, line_count-1)
                    output.append(
                        (date, subject, author, filename, range_tuple))
            # reset for the next email
            grepblock = ''
            block_startline = line_count
        grepblock += line
    f.close()
    return output

if __name__ == '__main__':
    if len(sys.argv) > 1:
        output = []
        for filename in sys.argv[1:]:
            output += parse_file(filename)
        output.sort(key=lambda x: x[0], reverse=True)
        for t in output:
            print('{0}\t{1}\t{2}\t{3}:{4[0]}-{4[1]}'.format(
                t[0].isoformat(), t[1], t[2], t[3], t[4]))
    else:
        print("USAGE: list of filenames of NEW-style nanog archive index "
             "files to process")