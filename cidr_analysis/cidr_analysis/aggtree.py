#!/usr/bin/env python2.6

"""Handles the aggregation and reporting aspects of the Cidr Report.

"""

import itertools
import os

import ipv4
from prefix_classes import PREFIX_CLASSES
import plot_tree


class PrefixAttr(object):
    """An object representing peer-specific attributes for a given prefix, such
    as AS_PATH, classification, etc. These have a many-to-1 association with
    CidrPrefix objects.

    """
    def __init__(self, as_path, is_advertised=True,
        prefix_class=PREFIX_CLASSES.LONELY):
        self.as_path = as_path
        self.is_advertised = is_advertised
        self.prefix_class = prefix_class
        self.adv_children = 0
        self.agg_children = 0


class CidrPrefix(object):
    """An object representing a route to a CIDR prefix, including AS_PATH(s)
    seen from peers to the observation AS, and metadata about the type of prefix
    and whether (and how) aggregable this prefix is if it is a covering prefix.

    """
    def __init__(self, prefix=0, prefix_len=0, ms_0=None, ms_1=None):
        self.prefix = prefix
        self.prefix_len = prefix_len
        # 'ms' == 'more specific', referring to the child prefixes of this
        # current prefix. the 0/1 refers to whether the least-significant bit
        # of the child prefix is a 0 or a 1
        self.ms_0 = ms_0
        self.ms_1 = ms_1
        # dict of PrefixAttrs indexed by peer's integer IP address
        # an empty attrs dict is taken to mean that the prefix isn't advertised
        self.attrs = {}
        self.origin_as = None
        # TODO should these be here?
        self.is_advertised = False
        self.adv_children = 0
        self.agg_children = 0

    def __str__(self):
        if self.attrs:
            return ipv4.int_to_dotquad(self.prefix) + '/' + str(self.prefix_len)
        else:
            return '<' + ipv4.int_to_dotquad(self.prefix) + '/' + \
                str(self.prefix_len) + '>'

    def __repr__(self):
        return self.__str__()

    def add_route(self, peer_ip_int, as_path):
        assert peer_ip_int not in self.attrs
        self.attrs[peer_ip_int] = PrefixAttr(as_path)


def debug_print(string):
    """Quick and dirty bit of indirection to allow debug-related printing to be
    disabled or reidrected later."""
    print(string)


def aggregate_table(infile):
    """Top-level function that accepts a properly formatted text-based routing
    table as infile, performs the Cidr Report aggregation on it, and outputs
    a Cidr Report-like output table.

    """
    as_agg_count_dict = {}
    as_netsnow_dict = {}
    for root in process_table(infile):
        # add_prefix_tree_to_netsnow_count also sets CidrPrefix.origin_as
        # attributes appropriately
        # TODO should origin_as be a separate function?
        add_prefix_tree_to_netsnow_count(as_netsnow_dict, root)
        (prefix_agg_list, prefix_adv_list) = classify_prefixes(root)
        as_agg_dict = group_agg_prefixes_by_origin_as(prefix_agg_list)
        count_agg_prefixes_by_as(as_agg_count_dict, as_agg_dict)

        ## debugging/verbose stuff:
        debug_print(prefix_agg_list)
        debug_print(len(prefix_agg_list))
        debug_print(prefix_adv_list)
        debug_print(len(prefix_adv_list))
        best_agg_list = []
        for k in root.attrs:
            best_agg_list.append((k, root.attrs[k].as_path[-1],
                root.attrs[k].agg_children, root.attrs[k].adv_children))
        best_agg_list.sort(key=lambda x: x[2], reverse=True)
        for t in best_agg_list:
            debug_print("{0[1]}\t(-{0[2]}, +{0[3]})\t{0[0]}".format(t))
        debug_print(root.agg_children)
        debug_print(root.adv_children)
        if root.prefix >> 24 == 17:
            print prefix_agg_list
            print as_agg_dict
            netsnow = [x for x in as_netsnow_dict.iteritems()]
            netsnow.sort(key=lambda x: x[1], reverse=True)
            for k in xrange(len(netsnow)):
                print netsnow[k]
            plot_tree.plot_tree(root, os.path.realpath('./plots/'))
            break
    debug_print(as_agg_dict)
    print_new_cidr_report(as_agg_count_dict, as_netsnow_dict)


def process_table(infile):
    """
    Generator function that processes the contents of the text-formatted
    routing table given by file-like object infile and yields a prefix tree,
    rooted at a /8 prefix, for later processing.

    Infile Format Specification:
    The contents of the input text file assume the following format:

        X.X.X.X/L Y.Y.Y.Y AS0 AS1 AS2 ... ASN<EOL>

    where X.X.X.X is the prefix, L is the prefix length, Y.Y.Y.Y is address of
    the peer that observed this route, and ASi for i=0..N is the AS path, with
    AS0 being the origin AS (i.e. in reverse order compared to the Cisco CLI).

    Further, the input text file is assumed to be organized such that routes
    with prefixes having the same first octet are in continguous blocks. This
    organization of the text file is required to enable this generator function
    to behave as advertised.

    Arguments:
    infile -- a file-like object where each line is a routing table entry in
    the format specified above.

    Returns:
    an iterator-like object that, when next() is called, returns the next prefix
    tree corresponding to the next /8 encountered in the input file.

    """
    line_count = 0
    current_prefixstr = ''
    current_cidrprefix = None
    current_slash8 = None  # first octet of the current /8
    slash8_root = None  # root of the prefix tree for the current /8

    # This loop iterates line-by-line through the file, and contains two levels
    # of state.
    # The first is at a prefix-level of granularity and exists to
    # create a new CidrPrefix object for each new prefix and then add the
    # remaining routes observed for the same prefix to that same CidrPrefix
    # object.
    # The second is at a /8 level and is the level of granularity at which the
    # generator function operates, yielding the current prefix tree when the
    # next /8 is encountered.
    for line in infile:
        components = line.split()
        if current_prefixstr != components[0]:
            slash8_root = add_cidrprefix_to_tree(slash8_root,
                current_cidrprefix)
            # create new prefix object
            current_prefixstr = components[0]
            [prefix, prefix_len] = current_prefixstr.split('/')
            prefix = ipv4.dotquad_to_int(prefix)
            prefix_len = int(prefix_len)
            current_cidrprefix = CidrPrefix(prefix, prefix_len)
            # yield slash8 to caller if new prefix is also new /8
            if current_slash8 != prefix >> 24:
                if slash8_root:
                    yield slash8_root
                current_slash8 = prefix >> 24
                slash8_root = None
                debug_print("current_slash8 = {0}".format(current_slash8))
        # add route (prefix-asn pair) for the given prefix
        peer_ip = ipv4.dotquad_to_int(components[1])
        as_path = [int(asn) for asn in components[2:]]
        current_cidrprefix.add_route(peer_ip, as_path)
        # debug info
        line_count += 1
        if line_count % 1000 == 0:
            debug_print(line_count)

    # after EOF, yield remaining data before returning
    slash8_root = add_cidrprefix_to_tree(slash8_root, current_cidrprefix)
    if slash8_root:
        yield slash8_root


def add_cidrprefix_to_tree(root, cidrprefix):
    """Adds a given CidrPrefix to a prefix tree. If the root is not defined, a
    new real or 'virtual' root is instantiated if the cidrprefix is or is not
    a /8, respectively. If the root is defined, the prefix is simply inserted
    into the tree.

    The root of the tree is returned, and should always be used in the case that
    the root is redefined due to the creation of a new tree or encountering of a
    /8 in the routing table.

    """
    if cidrprefix:
        if cidrprefix.prefix_len == 8:
            assert root is None  # otherwise we need to merge this
            root = cidrprefix
        elif cidrprefix.prefix_len > 8:
            if not root:  # create virtual /8 node
                root = CidrPrefix(cidrprefix.prefix & 0xFF000000, 8)
            insert_prefix_into_tree(root, cidrprefix)
        else:  # less specific than /8: ignore (or log for debugging)
            pass
    return root


def insert_prefix_into_tree(root, new):
    """Insert new CidrPrefix to the prefix tree rooted at root by walking the
    tree and adding 'virtual' nodes as necessary to place the prefix in the
    correct location in the binary prefix tree.

    """
    cursor = root
    test_mask = 0x00800000
    for i in xrange(9, new.prefix_len+1):
        if test_mask & new.prefix > 0:
            if i == new.prefix_len:
                if cursor.ms_1:
                    assert cursor.ms_1.attrs is None
                    new.ms_0 = cursor.ms_1.ms_0
                    new.ms_1 = cursor.ms_1.ms_1
                cursor.ms_1 = new
            else:
                if not cursor.ms_1:
                    cursor.ms_1 = CidrPrefix(
                        prefix=(cursor.prefix | test_mask), prefix_len=i)
            cursor = cursor.ms_1
        else:
            if i == new.prefix_len:
                if cursor.ms_0:
                    assert cursor.ms_0.attrs is None
                    new.ms_0 = cursor.ms_0.ms_0
                    new.ms_1 = cursor.ms_0.ms_1
                cursor.ms_0 = new
            else:
                if not cursor.ms_0:
                    cursor.ms_0 = CidrPrefix(prefix=cursor.prefix, prefix_len=i)
            cursor = cursor.ms_0
        test_mask >>= 1


def classify_prefixes(prefix, parent=None, ancestor_attrs={}):
    # TODO default ancestor_attrs={} is dangerous, even though I'm using it
    # correctly -- think about changing this
    """For a given constructed prefix tree, traverse the tree and classify its
    prefixes as LONELY/TOP/DEAGGREGATED/DELEGATED and also update counts of
    how many of each prefixes children may be aggregated (i.e. unannounced) and
    how many must be announced.

    The algorithm behind this function performs a recursive DFS traversal of the
    tree to find each leaf node and then work back up the tree comparing each
    child for aggregability against its parents.

    Returns a tuple containing a list of the prefixes in the tree that may be
    aggregated and a list of the prefixes that must still be announced in a
    fully aggregated routing table.

    """
    agg_list = []
    adv_list = []

    # Classification of child prefixes relies on knowledge of ancestor prefix
    # attributes. This serves to make the most recently encountered ('lowest',
    # in tree terms) attributes from each peer available at the current prefix.
    if prefix.attrs:
        new_ancestor_attrs = ancestor_attrs.copy()
        new_ancestor_attrs.update(prefix.attrs)
    else:
        new_ancestor_attrs = ancestor_attrs

    if prefix.ms_0:
        if prefix.attrs:
            (agg, adv) = classify_prefixes(prefix.ms_0, prefix, new_ancestor_attrs)
        else:
            (agg, adv) = classify_prefixes(prefix.ms_0, parent, new_ancestor_attrs)
        agg_list += agg
        adv_list += adv
    if prefix.ms_1:
        if prefix.attrs:
            (agg, adv) = classify_prefixes(prefix.ms_1, prefix, new_ancestor_attrs)
        else:
            (agg, adv) = classify_prefixes(prefix.ms_1, parent, new_ancestor_attrs)
        agg_list += agg
        adv_list += adv

    # base case -- we've hit bottom and are working back up the tree
    if parent and prefix.attrs:
        fully_aggregable = True
        peer_set = set(ancestor_attrs).union(set(prefix.attrs))
        for k in peer_set:  # TODO could be simplified to just ancestor_attrs
            if k not in ancestor_attrs:
                # TODO log this
                debug_print("orphan prefix-peer combo")
            else:
                anc_attr = ancestor_attrs[k]
                try:
                    des_attr = prefix.attrs[k]
                    if anc_attr.prefix_class == PREFIX_CLASSES.LONELY:
                        anc_attr.prefix_class = PREFIX_CLASSES.TOP
                    if anc_attr.as_path == des_attr.as_path:
                        des_attr.prefix_class = PREFIX_CLASSES.DEAGG
                        des_attr.is_advertised = False
                        anc_attr.agg_children += 1
                    else:
                        des_attr.prefix_class = PREFIX_CLASSES.DELEG
                        des_attr.is_advertised = True
                        anc_attr.adv_children += 1
                        fully_aggregable = False
                    anc_attr.agg_children += des_attr.agg_children
                    anc_attr.adv_children += des_attr.adv_children
                except KeyError:
                    pass

        # time to make a generalization about the prefix based on each
        # table's view of that prefix
        if fully_aggregable:
            agg_list.append(prefix)
            prefix.is_advertised = False
            parent.agg_children += 1
        else:
            adv_list.append(prefix)
            prefix.is_advertised = True
            parent.adv_children += 1
        parent.agg_children += prefix.agg_children
        parent.adv_children += prefix.adv_children

    return (agg_list, adv_list)


def group_agg_prefixes_by_origin_as(prefix_agg_list):
    """Takes a list of aggregable prefixes gathered by another function and
    groups these prefixes into a dictionary by the origin AS of each prefix
    which is then returned.
    
    The dictionary is keyed on origin AS number, and the value associated with
    each key is a list of the aggregable prefixes originated by the key ASN.
    
    """
    as_agg_dict = {}  # keyed on AS number
    for prefix in prefix_agg_list:
        as_agg_dict.setdefault(prefix.origin_as, []).append(prefix)
    return as_agg_dict


def count_agg_prefixes_by_as(as_agg_count_dict, as_agg_dict):
    """Updates as_agg_count_dict, the dictionary containing a count of the
    number of aggregable prefixes advertised by each AS, based on the prefixes
    in as_agg_dict.
    
    Returns the updated as_agg_count_dict, which is also modified in place, so
    the return doesn't need to be used.
    
    """
    for asn in as_agg_dict:
        as_agg_count_dict[asn] = as_agg_count_dict.get(asn, 0) + sum(
            (p.agg_children for p in as_agg_dict[asn]))
    return as_agg_count_dict


def add_prefix_tree_to_netsnow_count(as_netsnow_dict, root):
    """Add all of the prefixes in the prefix tree rooted at root to the
    netsnow dict. The netsnow dict contains a count of the total prefixes
    currently in the routing table originated by each AS number.

    This function also determines the origin_as attribute of each CidrPrefix
    object it encounters, setting it to the origin AS if the prefix is
    originated by a single AS from all available vantage points, or -1 if it
    is originated by multiple AS numbers (i.e the prefix has multiple origin
    ASes, or 'MOAS')

    """
    if root.attrs:
        origin_set = set()
        for attr in root.attrs.itervalues():
            origin_set.add(attr.as_path[0])
        if len(origin_set) == 1:
            root.origin_as = origin_set.pop()
        else:  # MOAS -- TODO find a better solution
            # TODO consider origin_as = set/list of origins, instead of -1
            root.origin_as = -1
        as_netsnow_dict[root.origin_as] = as_netsnow_dict.get(
            root.origin_as, 0) + 1
    if root.ms_0:
        add_prefix_tree_to_netsnow_count(as_netsnow_dict, root.ms_0)
    if root.ms_1:
        add_prefix_tree_to_netsnow_count(as_netsnow_dict, root.ms_1)


def print_new_cidr_report(as_agg_count_dict, as_netsnow_dict, top_n=30):
    """Print the "top N" Cidr Report in the format that Geoff Huston emails
    out weekly to the operator communities. This function prints out the top
    top_n prefixes, sorted in decreasing order by their NetGain -- the
    absolute improvement they could offer in terms of global prefix counts by
    aggregating their routing table as much as possible.

    """
    as_agg_list = [x for x in as_agg_count_dict.iteritems()]
    as_agg_list.sort(key=lambda x: x[1], reverse=True)

    print(" --- 12Nov10 ---")
    print("ASnum   NetsNow     NetsAggr    NetGain     % Gain")
    # example format, showing field width and justification:
    #
    #      [8     ][     8][4 ][     8][4 ][     8][4 ][     8]
    #      ASnum   NetsNow     NetsAggr    NetGain     % Gain
    #      19262     340775      208585      132170       38.8%

    tbl_netgain = sum((x[1] for x in as_agg_list))
    tbl_netsnow = sum(as_netsnow_dict.itervalues())
    tbl_netsaggr = tbl_netsnow - tbl_netgain
    try:
        tbl_pctgain = 100.0*float(tbl_netgain)/float(tbl_netsnow)
    except ZeroDivisionError:
        tbl_pctgain = -100.0
    print("{0:<8}{1:>8}    {2:>8}    {3:>8}    {4:>8.3}%\n".format(
        "Table", tbl_netsnow, tbl_netsaggr, tbl_netgain, tbl_pctgain))

    sum_netsnow = 0
    sum_netsaggr = 0
    sum_netgain = 0
    for i in xrange(min(len(as_agg_list), top_n)):
        as_num = as_agg_list[i][0]
        netgain = as_agg_list[i][1]
        netsnow = as_netsnow_dict[as_num]
        netsaggr = netsnow - netgain
        try:
            pctgain = 100.0*float(netgain)/float(netsnow)
        except ZeroDivisionError:
            pctgain = -100.0
        print("{0:<8}{1:>8}    {2:>8}    {3:>8}    {4:>8.3}%".format(
            as_num, netsnow, netsaggr, netgain, pctgain))
        sum_netsnow += netsnow
        sum_netsaggr += netsaggr
        sum_netgain += netgain

    try:
        sum_pctgain = 100.0*float(sum_netgain)/float(sum_netsnow)
    except ZeroDivisionError:
        sum_pctgain = -100.0
    print("\n{0:<8}{1:>8}    {2:>8}    {3:>8}    {4:>8.3}%".format(
        "Total", sum_netsnow, sum_netsaggr, sum_netgain, sum_pctgain))