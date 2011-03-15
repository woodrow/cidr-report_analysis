#!/usr/bin/python2.6

import sys
import re
import pickle
import pprint

count_list = []
for filepath in sys.argv[1:]:
    match = re.search("(\d{8})", filepath)
    if match:
        date_str = '-'.join([match.groups()[0][0:4], match.groups()[0][4:6], match.groups()[0][6:8]])
    else:
        match = re.search("(\d{4}-\d{2}-\d{2})", filepath)
        date_str = match.groups()[0]
    peer_counts = []
    f = open(filepath)
    for line in f:
        peer_counts.append(int(line.split()[0]))
    f.close()
    if len(peer_counts) % 2 == 1:
        median = peer_counts[len(peer_counts)/2]
    else:
        median = (peer_counts[len(peer_counts)/2] + peer_counts[len(peer_counts)/2 - 1])/2
    count_list.append((date_str, median, max(peer_counts)))
count_list.sort(key=lambda x: int(re.sub('-', '', x[0])))
f = open('peer_counts.csv', 'w')
f.write("date,median,max\n")
for item in count_list:
    f.write("{0[0]},{0[1]},{0[2]}\n".format(item))
f.close()
pprint.pprint(count_list)
pf = open('peer_counts.pickle', 'w')
pickle.dump(count_list, pf)
pf.close()
