#!/usr/bin/env python2.6

import os
import sys

BGPDUMP_PATH = os.path.realpath(
    '../libbgpdump/libbgpdump-1.4.99.13/2testbgpdump')

if 1 < len(sys.argv) < 3:
    full_path = os.path.realpath(sys.argv[1])
    dir_name = os.path.dirname(full_path)
    base_name = '.'.join(os.path.basename(full_path).split('.')[:-1])

    txt_name = os.path.join(dir_name, base_name) + '.txt'
    peers_name = os.path.join(dir_name, base_name) + '.peers'

    if not os.path.exists(txt_name):
        os.system(' '.join([BGPDUMP_PATH, '-d 0', full_path, txt_name]))

    # TODO this will need to be adjusted if I consider (peer_ip,peer_as)
    os.system(' '.join(["awk '{print $2}'", txt_name,
        '| sort | uniq -c | sort -r -n >', peers_name]))

else:
    print(' '.join(["Usage:", sys.argv[0], 'MRT_RIB_FILE']))
    print("Produces intermediate text-based routing table (.txt) and peer "
          "table (.peer) based on supplied MRT_RIB_FILE.")
