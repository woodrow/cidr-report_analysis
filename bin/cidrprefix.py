#!/usr/bin/env python

import dpkt
#import pybgpdump  # XXX pybgpdump currently only support IPv4 BGP UPDATEs
import pybgptable  # XXX pybgptable only supports IPv4 TABLE_DUMP (not _V2)

class Enumerate(object):
    def __init__(self, *args):
        if len(args) < 1:
            raise TypeError("Enumerate.__init() takes at least 1 argument "
                "(0 given)")
        if len(args) == 1:
            if args[0] == str(args[0]):
                namelist = args[0].split()
            else:
                namelist = args[0]
        else:
            namelist = [str(x) for x in args]
        for number, name in enumerate(namelist):
            setattr(self, name, number)

PREFIX_CLASSES = Enumerate('LONELY', 'TOP', 'DEAGG', 'DELEG')

class CidrPrefix:
    def __init__(self, address=0, prefix_len=0, as_path=None, 
        more_specific0=None, more_specific1=None, less_specific=None,
        is_aggregable=True, prefix_class=PREFIX_CLASSES.LONELY):
        self.address = address
        self.prefix_len = prefix_len

        self.as_path = as_path  # a list of integers with origin in index 0

        self.more_specific0 = more_specific0
        self.more_specific1 = more_specific1
        self.less_specific = less_specific
        
        self.is_aggregable = is_aggregable
        self.aggregable_more_specifics = 0
        self.prefix_class = prefix_class

def dotquad_to_int(ipv4_str):
    ipv4_int = 0
    byte_str_list = ipv4_str.split('.')
    if len(byte_str_list) != 4:
        raise ValueError("dotquad_to_int takes address in dotted quad format")
    for pos, byte_str in enumerate(byte_str_list):
        ipv4_int |= int(byte_str) << (3-pos)*8
    return ipv4_int

DELIMS = ( ('', ''),
           ('{', '}'),  # AS_SET
           ('', ''),    # AS_SEQUENCE
           ('(', ')'),  # AS_CONFED_SEQUENCE
           ('[', ']') ) # AS_CONFED_SET

def path_to_str(path):
    path_str = ''
    for seg in path.segments:
        path_str += DELIMS[seg.type][0]
        for asn in seg.path:
            path_str += '%d ' % (asn)
        path_str = path_str[:-1]
        path_str += DELIMS[seg.type][1] + ' '
    return path_str

def process_table():
    dfz_table = pybgptable.BGPTable('rib_dumps/rib.20101015.0000.bz2')
    for (mrt_h, td) in dfz_table:
        for entry in td.rib_entries:
            for attr in entry.attributes:
#                print(attr.type)
                if attr.type == dpkt.bgp.AS_PATH:
#                    print(path_to_str(attr.as_path))
                    break

"""
What needs to happen:
- process list one entry at a time:
    - adding them to the tree, constructing intermediate tree elements
      as necessary to get to that point
    - classify according to Cittadini et al: TOP, DEAGG, DELEG, LONELY
        - LONELY by default
        - anything more specifc under lonely: LONELY -> TOP
        - anything goes under a less specific: LONELY ->
            - DEAGG if the AS_PATH is same as immediate less-specific cover
            - DELEG if the AS_PATH is NOT same as immediate less-specific cover
                - AND all less-specific covers aggregable = False
                - AND subtract aggregable_more_specifics from parent
- one tree per vantage point (receiver/peer AS)
    - pick one to start with -- i.e. 3356
- finally, walk the tree, looking for TOPs
    - for each subtree rooted at a TOP, determine if 
"""

def main():
    #ipv4_tree = CidrPrefix()
    print("Starting processing table.")
    process_table()
    print("Ending processing table.")

if __name__ == '__main__':
    main()