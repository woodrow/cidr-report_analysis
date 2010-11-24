#!/usr/bin/env python2.6

import os
import sys
import re

BGPDUMP_PATH = os.path.realpath(
    '../libbgpdump/libbgpdump-1.4.99.13/simpledump')

def main():
    peer_ip_arg = ''

    if 1 < len(sys.argv) < 4:
        if len(sys.argv) == 2:
            full_path = os.path.realpath(sys.argv[1])
        else:
            if sys.argv[1] == '-p':
                peer_ip_arg = '-p'
            else:
                usage()
                exit()
            full_path = os.path.realpath(sys.argv[2])

        dir_name = os.path.dirname(full_path)
        base_name = '.'.join(os.path.basename(full_path).split('.')[:-1])

        txt_name = os.path.join(dir_name, base_name) + '.txt'
        peers_name = os.path.join(dir_name, base_name) + '.peers'
        #prefixes per as, per peer
        ppapp_name = os.path.join(dir_name, base_name) + '.ppapp'

        if not os.path.exists(txt_name):
            print("Generating .txt routing table.")
            os.system(' '.join(
                [BGPDUMP_PATH, peer_ip_arg, full_path, txt_name]))

        # TODO process AS_SETs
        # TODO remove private AS numbers

        # check if this contains (prefix, AS_PATH) or (prefix, peer_ip, AS_PATH)
        f = open(txt_name)
        if re.search('((?:\d{1,3}\.){3}\d{1,3})',
            f.readline().split(' ')[1]) is not None:
            args_peers = ' '.join(["awk '{print \"(\" $3, $2 \")\"}'",
                txt_name, '| sort | uniq -c | sort -r -n >', peers_name])
            args_ppapp = ' '.join(["awk '{print \"(\" $3, $2 \")\", $NF}'",
                txt_name, '| sort | uniq -c | sort -n -k 4 -s >', ppapp_name])
        else:
            args_peers = ' '.join(["awk '{print $2}'", txt_name,
                '| sort | uniq -c | sort -r -n >', peers_name])
            args_ppapp = ' '.join(["awk '{print $2, $NF}'",
                txt_name, '| sort | uniq -c | sort -n -k 3 -s >', ppapp_name])
        f.close()
        print("Generating .peers file.")
        os.system(args_peers)
        print("Generating .ppapp file.")
        os.system(args_ppapp)

    else:
        usage()

def usage():
    print(' '.join(["Usage:", sys.argv[0], '[-p] MRT_RIB_FILE']))
    print("""Produces intermediate text-based routing table (.txt) and peer
table (.peer) based on supplied MRT_RIB_FILE.

Optional flag -p will include peer ip addresses to determine unique neighbors.
This only has effect if the intermediate text-based routing table (.txt) file
doesn't yet exist.
""")

if __name__ == '__main__':
    main()
