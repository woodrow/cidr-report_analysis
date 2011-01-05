#!/usr/bin/env python2.6

import itertools
from enumerator import Enumerate
import ipv4

PREFIX_CLASSES = Enumerate('LONELY', 'TOP', 'DEAGG', 'DELEG')

class PrefixAttr(object):
    def __init__(self, as_path, is_aggregable=False,
        prefix_class=PREFIX_CLASSES.LONELY):
        self.as_path = as_path
        self.is_aggregable = is_aggregable
        self.aggregable_more_specifics = 0
        self.prefix_class = prefix_class


class CidrPrefix(object):
    """An object representing a route to a CIDR prefix, including AS_PATH(s)
    seen from peers to the observation AS, and metadata about the type of prefix
    and whether (and how) aggregable this prefix is if it is a covering prefix.

    """
    def __init__(self, prefix=0, prefix_len=0, ms_0=None, ms_1=None):
        self.prefix = prefix
        self.prefix_len = prefix_len

        self.attrs = {} # dictionary of PrefixAttrs indexed by peer IP address

        self.ms_0 = ms_0
        self.ms_1 = ms_1

        # TODO not sure if this is a good idea to keep here and update
        # during processing?
        self.prefix_class = PREFIX_CLASSES.LONELY
        self.is_aggregable = False
        self.aggregable_more_specifics = 0
        self.origin_as = None

        # used later, by post-processing functions
        self.post_is_aggregable = False
        self.post_ams = None
        self.post_origin_as = None

    def __str__(self):
        if self.attrs:
            return ipv4.int_to_dotquad(self.prefix) + '/' + str(self.prefix_len)
        else:
            return '<' + ipv4.int_to_dotquad(self.prefix) + '/' + \
                str(self.prefix_len) + '>'

    def __repr__(self):
        return self.__str__()

    def add_route(self, peer_ip_int, as_path, is_aggregable=False):
        assert peer_ip_int not in self.attrs
        self.attrs[peer_ip_int] = PrefixAttr(as_path, is_aggregable)
        if not self.origin_as:
            self.origin_as = as_path[0]
        elif self.origin_as != as_path[0]:
            self.origin_as = 0
        # TODO if is_aggregable: self.is_aggregable = True


def aggregate_table(infile):
    as_agg_count_dict = {}
    as_netsnow_dict = {}
    for root in process_table(infile):
            # also sets root.post_origin_as appropriately
            add_prefix_tree_to_netsnow_count(as_netsnow_dict, root)

            prefix_agg_list = find_aggregable_prefixes(root)
            as_agg_dict = group_agg_prefixes_by_as(prefix_agg_list)
            count_agg_prefixes_by_as(as_agg_count_dict, as_agg_dict)
            ## debug; if used to go here
#            if root.prefix >> 24 == 17:
#                print prefix_agg_list
#                print as_agg_dict
#                netsnow = [x for x in as_netsnow_dict.iteritems()]
#                netsnow.sort(key=lambda x: x[1], reverse=True)
#                for k in xrange(len(netsnow)):
#                    print netsnow[k]
#                plot_tree(root)
#                break
    print_new_cidr_report(as_agg_count_dict, as_netsnow_dict)


def process_table(infile):
    """TODO NOTE ABOUT GENERATOR FUNCTION
    Process the contents of the text-formatted routing table and form a
    prefix tree for later processing, storing the output in root_list which
    contains the prefix tree corresponding to each /8 in the IPv4 address space.

    The input text file is assumed to be in contiguous blocks organized by
    prefix to keep things efficient.

    Arguments
    infile -- a file-like object where each line is a routing table entry in
    PREFIX AS_PATH format

    Returns
    an iterator-like object that, when next() is called, returns the next root
    of an aggregation

    """
    line_count = 0
    current_prefixstr = ""
    current_slash8 = None  # first octet of the current /8
    new_cidrprefix = None
    slash8_root = None

    for line in infile:
        # line format: prefix/prefix_len peer_ip space-delimited-as_path
        components = line.split()
        if current_prefixstr != components[0]: # we've encountered a new prefix
            # add old prefix to tree
            slash8_root = add_cidrprefix_to_tree(slash8_root, new_cidrprefix)
            # create new prefix object
            current_prefixstr = components[0]
            [prefix, prefix_len] = current_prefixstr.split('/')
            prefix = ipv4.dotquad_to_int(prefix)
            prefix_len = int(prefix_len)
            new_cidrprefix = CidrPrefix(prefix, prefix_len)
            # yield slash8 to caller if new prefix is also new /8
            if current_slash8 != prefix >> 24:
                if slash8_root:
                    yield slash8_root
                current_slash8 = prefix >> 24
                slash8_root = None
                print("current_slash8 = {0}".format(current_slash8))
        # add route
        peer_ip = ipv4.dotquad_to_int(components[1])
        as_path = [int(asn) for asn in components[2:]]
        new_cidrprefix.add_route(peer_ip, as_path, is_aggregable=True)
        # debug info
        line_count += 1
        if line_count % 1000 == 0:
            print line_count

    # after the loop, yield remaining data before returning
    slash8_root = add_cidrprefix_to_tree(slash8_root, new_cidrprefix)
    if slash8_root:
        yield slash8_root


def add_cidrprefix_to_tree(root, cidrprefix):
    if cidrprefix:
        if cidrprefix.prefix_len == 8:
            root = cidrprefix
        elif cidrprefix.prefix_len > 8:
            if not root:  # create virtual /8 node
                root = CidrPrefix(cidrprefix.prefix & 0xFF000000, 8)
            insert_prefix_into_tree(root, cidrprefix)
        else:  # less specific than /8: ignore (or log for debugging)
            pass
    return root


def insert_prefix_into_tree(root, new):
    """Add node new to the prefix tree rooted at root. Update all ancestor nodes
    traversed from root to the proper location of new.

    """
    cursor = root
    test_mask = 0x00800000
    for i in xrange(9, new.prefix_len+1):
        update_ancestor(cursor, new)
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


def update_ancestor(ancestor, descendant):
    """Update ancestor's metadata to be consistent with the fact that descendant
    is now a descendant of ancestor, which may affect ancestor's aggregation
    potential, etc.

    """
    """
    TODO: I could do something clever here whereby i keep track of the last
    AS_PATH seen by a virtual node in the tree, and if no other AS_PATH is added
    to the subtree, then it could indeed be aggregated at this higher block.
    """

    # optimization to make tree-walking faster later on
    # also sort of a hack to allow using existing code that doesn't know about
    # CidrPrefix.attrs
    greatest_ancestor_class = ancestor.prefix_class
    greatest_descendant_class = descendant.prefix_class
    greatest_agg_more_specifics = ancestor.aggregable_more_specifics

    for k in ancestor.attrs:
        try:
            anc_attr = ancestor.attrs[k]
            des_attr = descendant.attrs[k]
            if anc_attr.prefix_class == PREFIX_CLASSES.LONELY:
                anc_attr.prefix_class = PREFIX_CLASSES.TOP
                greatest_ancestor_class = max(                    # optimization
                    greatest_ancestor_class, PREFIX_CLASSES.TOP)
            #if as_paths_match(ancestor, descendant):
            if anc_attr.as_path == des_attr.as_path:
                des_attr.prefix_class = PREFIX_CLASSES.DEAGG
                greatest_descendant_class = max(                  # optimization
                    greatest_descendant_class, PREFIX_CLASSES.DEAGG)
                if anc_attr.is_aggregable:
                    anc_attr.aggregable_more_specifics += 1
                    greatest_agg_more_specifics = max(
                        greatest_agg_more_specifics,
                        anc_attr.aggregable_more_specifics)
            else:
                des_attr.prefix_class = PREFIX_CLASSES.DELEG
                greatest_descendant_class = max(                  # optimization
                    greatest_descendant_class, PREFIX_CLASSES.DELEG)
                if anc_attr.is_aggregable:
                    anc_attr.is_aggregable = False
                    anc_attr.aggregable_more_specifics = 0
        except KeyError:
            pass

    # optimization + reuse existing code hack
    ancestor.prefix_class = greatest_ancestor_class
    descendant.prefix_class = greatest_descendant_class
    if descendant.prefix_class == PREFIX_CLASSES.DELEG:
        ancestor.is_aggregable = False
        ancestor.aggregable_more_specifics = 0
    elif descendant.prefix_class == PREFIX_CLASSES.DEAGG:
        ancestor.is_aggregable = True
        ancestor.aggregable_more_specifics = greatest_agg_more_specifics


def find_aggregable_prefixes(root):
    prefix_agg_list = []
    _find_aggregable_prefixes_recursor(root, prefix_agg_list)
    return prefix_agg_list


def _find_aggregable_prefixes_recursor(tree, prefix_agg_list):
    if tree.attrs and all((a.is_aggregable for a in tree.attrs.itervalues())):
#        print('YES')
        max_agg = max(
            (a.aggregable_more_specifics for a in tree.attrs.itervalues()))
        if max_agg > 0:
#            print('DOUBLE-YES')
            tree.post_is_aggregable = True
            tree.post_ams = max_agg
            prefix_agg_list.append(tree)
        else:
            tree.post_ams = 0
    else:
        if tree.attrs:
            tree.post_ams = 0
        if tree.ms_0:
            _find_aggregable_prefixes_recursor(tree.ms_0, prefix_agg_list)
        if tree.ms_1:
            _find_aggregable_prefixes_recursor(tree.ms_1, prefix_agg_list)


def group_agg_prefixes_by_as(prefix_agg_list):
    as_agg_dict = {}  # keyed on as number
    for prefix in prefix_agg_list:
        as_agg_dict.setdefault(prefix.post_origin_as, []).append(prefix)
        ## could also implement this as adding to set + checking set size --
        ## performance comparison opportunity?
        #origin_set = set()
        #for attr in prefix.attrs.itervalues():
        #    origin_set.add(attr.as_path[0])
        #if len(origin_set) == 1:
        #    prefix.post_origin_as = origin_set.pop()
        #    as_agg_dict.setdefault(prefix.post_origin_as, []).append(prefix)
        #else:
        #    print("MOAS!!")
        #    prefix.post_origin_as = -1
        ################################################
        # prefix_attr_iter = prefix.attrs.itervalues()
        # test_origin = prefix_attr_iter.next().as_path[0]
        # origins_match = True
        # for attr in prefix_attr_iter:
        #     if attr.as_path[0] != test_origin:
        #         origins_match = False
        #         break
        # if origins_match:
        #     prefix.post_origin_as = test_origin
        #     as_agg_dict.setdefault(test_origin, []).append(prefix)
        # else:
        #     print("MOAS!!")
        #     #prefix.post_origin_as = 0
        #     #as_agg_dict.setdefault(0, []).append(prefix)
    return as_agg_dict


def count_agg_prefixes_by_as(as_agg_count_dict, as_agg_dict):
    for asn in as_agg_dict:
        as_agg_count_dict[asn] = as_agg_count_dict.get(asn, 0) + sum(
            (p.post_ams for p in as_agg_dict[asn]))
    return as_agg_count_dict


def add_prefix_tree_to_netsnow_count(as_netsnow_dict, root):
    if root.attrs:
        origin_set = set()
        for attr in root.attrs.itervalues():
            origin_set.add(attr.as_path[0])
        if len(origin_set) == 1:
            root.post_origin_as = origin_set.pop()
        else:
#            print("MOAS!!")
            root.post_origin_as = -1
        as_netsnow_dict[root.post_origin_as] = as_netsnow_dict.get(
            root.post_origin_as, 0) + 1
    if root.ms_0:
        add_prefix_tree_to_netsnow_count(as_netsnow_dict, root.ms_0)
    if root.ms_1:
        add_prefix_tree_to_netsnow_count(as_netsnow_dict, root.ms_1)


def print_new_cidr_report(as_agg_count_dict, as_netsnow_dict, top_n=30):
    """
    [8     ][     8][4 ][     8][4 ][     8][4 ][     8]
    ASnum   NetsNow     NetsAggr    NetGain     %Gain
    19262     340775      208585      132170       38.8%
    """

    as_agg_list = [x for x in as_agg_count_dict.iteritems()]
    as_agg_list.sort(key=lambda x: x[1], reverse=True)

    print(" --- 12Nov10 ---")
    print("ASnum   NetsNow     NetsAggr    NetGain     % Gain")

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



################################################################################
##  OLD ALGORITHMS
##

def get_prefix_agg_list(root_list):
    prefix_agg_list = []
    for prefix in (x for x in root_list if x is not None):
        _get_prefix_agg_list_helper(prefix, prefix_agg_list)
    return prefix_agg_list

def _get_prefix_agg_list_helper(prefix, prefix_agg_list):
    if prefix.is_aggregable:
        if prefix.aggregable_more_specifics > 0:
            prefix_agg_list.append(prefix)
    else:
        if prefix.ms_0 is not None:
            _get_prefix_agg_list_helper(prefix.ms_0, prefix_agg_list)
        if prefix.ms_1 is not None:
            _get_prefix_agg_list_helper(prefix.ms_1, prefix_agg_list)

def get_as_agg_list(prefix_agg_list):
    as_agg_list = [(str(x), x.aggregable_more_specifics, x.origin_as)
        for x in prefix_agg_list]
    as_agg_list.sort(key=lambda x: x[2])
    as_aggregates = []
    for k, g in itertools.groupby(as_agg_list, lambda x: x[2]):
        as_aggregates.append((k, sum([x[1] for x in g])))
    as_aggregates.sort(key=lambda x: x[1], reverse=True)
    return as_aggregates

def get_as_netsnow_dict(root_list):
    as_netsnow_dict = {}
    for prefix in (x for x in root_list if x is not None):
        _get_as_netsnow_list_helper(prefix, as_netsnow_dict)
    return as_netsnow_dict

def _get_as_netsnow_list_helper(prefix, as_netsnow_dict):
    origin_set = set()
    for k in prefix.attrs:
        origin_set.add(prefix.attrs[k].as_path[0])
    for origin in origin_set:
        as_netsnow_dict[origin] = as_netsnow_dict.get(
            origin, 0) + 1
    if prefix.ms_0 is not None:
        _get_as_netsnow_list_helper(prefix.ms_0, as_netsnow_dict)
    if prefix.ms_1 is not None:
        _get_as_netsnow_list_helper(prefix.ms_1, as_netsnow_dict)

def print_cidr_report(as_agg_list, as_netsnow_dict, top_n=30):
    """
    [8     ][     8][4 ][     8][4 ][     8][4 ][     8]
    ASnum   NetsNow     NetsAggr    NetGain     %Gain
    19262     340775      208585      132170       38.8%
    """
    print(" --- 12Nov10 ---")
    print("ASnum   NetsNow     NetsAggr    NetGain     % Gain")

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

def plot_tree(root):
    import networkx as nx
    import matplotlib.pyplot as plt
    graph = nx.DiGraph()
    _plot_tree_helper(root, root, graph, 0, force=True)
    #twopi, gvcolor, wc, ccomps, tred, sccmap, fdp, circo, neato, acyclic, nop, gvpr, dot.
    #nodelist = [v for v in graph.nodes() if v.aggregable_more_specifics > 0]
    #node_color = [color_func(v.aggregable_more_specifics) for v in graph]
    #nx.draw_graphviz(graph, prog='dot', nodelist=nodelist, node_color=node_color)
    #nx.draw_graphviz(graph, nodelist=nodelist, node_color=node_color)
    nx.write_dot(graph, 'plot.dot')
    #plt.show()

def color_func(ams):
    if ams > 0:
        return 'g'
    else:
        return 'r'

def _plot_tree_helper(node, parent_node, graph, deep, force=False):
#    if deep > 8:
#        return None
    p = parent_node
    r = None

    if node.attrs:
        graph.add_node(node, shape='box', penwidth=2)
        if node.post_ams > 0:
            graph.node[node]['style'] = 'filled'
            graph.node[node]['fillcolor'] = 'palegreen'
        ##if node.prefix_class is PREFIX_CLASSES.LONELY:
        ##    graph.node[node]['color'] = 'black'
        ##elif node.prefix_class is PREFIX_CLASSES.TOP:
        ##    graph.node[node]['color'] = 'blue'
        ##elif node.prefix_class is PREFIX_CLASSES.DEAGG:
        ##    graph.node[node]['color'] = 'green'
        ##elif node.prefix_class is PREFIX_CLASSES.DELEG:
        ##    graph.node[node]['color'] = 'red'
#        else:
#            graph.node[node]['color'] = 'red'
        graph.node[node]['label'] = ' '.join([str(node),
            str(node.post_ams), str(node.post_origin_as)])
        ##graph.node[node]['label'] += '\\n'.join(
        ##    [str(ap) for ap in node.as_paths])
        #str(node.as_paths[0])
        # annotate
        p = node
        r = node
    elif force:
        graph.add_node(node, shape='box', color='grey', penwidth=2)
        p = node
        r = node
    else:
        graph.add_node(node, shape='point')
        graph.node[node]['label'] = ''
        p = node
        r = node

    if node.ms_0:
        child = _plot_tree_helper(node.ms_0, p, graph, deep+1)
        if child:
            graph.add_edge(p, child)
    if node.ms_1:
        child = _plot_tree_helper(node.ms_1, p, graph, deep+1)
        if child:
            graph.add_edge(p, child)

    return r