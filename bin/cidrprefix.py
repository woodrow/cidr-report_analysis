#!/usr/bin/env python

#import dpkt
##import pybgpdump  # XXX pybgpdump currently only support IPv4 BGP UPDATEs
#import pybgptable  # XXX pybgptable only supports IPv4 TABLE_DUMP (not _V2)

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
    def __init__(self, prefix=0, prefix_len=0, as_path=None,
        ms_0=None, ms_1=None, is_aggregable=True,
        prefix_class=PREFIX_CLASSES.LONELY):
        self.prefix = prefix
        self.prefix_len = prefix_len

        self.as_path = as_path  # a list of integers with origin in index 0

        self.ms_0 = ms_0
        self.ms_1 = ms_1

        self.is_aggregable = is_aggregable
        self.aggregable_more_specifics = 0
        self.prefix_class = prefix_class

    def __str__(self):
        if self.as_path is not None:
            return int_to_dotquad(self.prefix) + '/' + str(self.prefix_len)
        else:
            return '[' + int_to_dotquad(self.prefix) + '/' + \
                str(self.prefix_len) + ']'

    def __repr__(self):
        return self.__str__()

def dotquad_to_int(ipv4_str):
    ipv4_int = 0
    byte_str_list = ipv4_str.split('.')
    if len(byte_str_list) != 4:
        raise ValueError("dotquad_to_int takes address in dotted quad format")
    for pos, byte_str in enumerate(byte_str_list):
        ipv4_int |= int(byte_str) << (3-pos)*8
    return ipv4_int

def int_to_dotquad(ipv4_int):
    octets = []
    for i in xrange(4):
        octets.append(str(ipv4_int & 0xFF))
        ipv4_int >>= 8
    octets.reverse()
    return '.'.join(octets)

def process_table(infile, root, agg_list):
    line_count = 0
    for line in infile:
        components = line.split(' ')
        [prefix, prefix_len] = components[0].split('/')
        as_path = components[1:]
        as_path.reverse()
        new_prefix = CidrPrefix(dotquad_to_int(prefix), int(prefix_len),
            as_path)
        add_node_to_tree(root, new_prefix, agg_list)
        line_count += 1
        if line_count % 1000 == 0:
            print line_count
    return agg_list

def add_node_to_tree(root, new, agg_list):
    cursor = root
    test_mask = 0x80000000

    for i in xrange(1, new.prefix_len+1):
        update_ancestor(cursor, new, agg_list)
        if test_mask & new.prefix > 0:
            if cursor.ms_1 == None:
                if i == (new.prefix_len - 1):
                    cursor.ms_1 = new
                else:
                    cursor.ms_1 = CidrPrefix(prefix=(cursor.prefix | test_mask)
                    , prefix_len=i)
            cursor = cursor.ms_1
        else:
            if cursor.ms_0 == None:
                if i == (new.prefix_len - 1):
                    cursor.ms_0 = new
                else:
                    cursor.ms_0 = CidrPrefix(prefix=cursor.prefix, prefix_len=i)
            cursor = cursor.ms_0
        test_mask >>= 1

def update_ancestor(ancestor, descendant, agg_list):
    if ancestor.as_path is not None and descendant.as_path is not None:
        if ancestor.prefix_class == PREFIX_CLASSES.LONELY:
            ancestor.prefix_class = PREFIX_CLASSES.TOP

        if ancestor.as_path == descendant.as_path:
            descendant.prefix_class = PREFIX_CLASSES.DEAGG
            if ancestor.is_aggregable:
                # here's where we add the ancestor to the set of
                # aggregable prefixes
                if ancestor not in agg_list:  # this could be expensive...
                    agg_list.append(ancestor)
                ancestor.aggregable_more_specifics += 1
        else:
            descendant.prefix_class = PREFIX_CLASSES.DELEG
            if ancestor.is_aggregable:
                ancestor.is_aggregable = False
                ancestor.aggregable_more_specifics = 0
                # here's where we remove the ancestor to the set of
                # aggregable prefixes
                agg_list.remove(ancestor)

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

#def main():
if __name__ == '__main__':
    print("Starting processing table.")
    root = CidrPrefix()
    agg_list = []
    f = open('../routeviews/3356_table_out_2.txt')
    process_table(f, root, agg_list)
    print("Ending processing table.")

#if __name__ == '__main__':
#    main()