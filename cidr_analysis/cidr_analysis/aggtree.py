#!/usr/bin/env python2.6

import itertools
from enumerate import Enumerate
import ipv4

PREFIX_CLASSES = Enumerate('LONELY', 'TOP', 'DEAGG', 'DELEG')
DFZ_ASNS = [209, 701, 1239, 1299, 2828, 2914, 3356, 3549, 3561, 6453, 6461,
    7018]

class CidrPrefix(object):
    """An object representing a route to a CIDR prefix, including AS_PATH(s)
    seen from peers to the observation AS, and metadata about the type of prefix
    and whether (and how) aggregable this prefix is if it is a covering prefix.

    """
    def __init__(self, prefix=0, prefix_len=0, as_path=None,
        ms_0=None, ms_1=None, is_aggregable=False,
        prefix_class=PREFIX_CLASSES.LONELY):
        self.prefix = prefix
        self.prefix_len = prefix_len

        # as_paths is a list of as_path lists
        # each as_path is list of integers with origin in index 0
        if as_path:
            self.as_paths = [as_path]
            self.origin_as = as_path[0]
        else:
            self.as_paths = []
            self.origin_as = None

        self.ms_0 = ms_0
        self.ms_1 = ms_1

        self.is_aggregable = is_aggregable
        self.aggregable_more_specifics = 0
        self.prefix_class = prefix_class

    def __str__(self):
        if self.as_paths:
            return ipv4.int_to_dotquad(self.prefix) + '/' + str(self.prefix_len)
        else:
            return '<' + ipv4.int_to_dotquad(self.prefix) + '/' + \
                str(self.prefix_len) + '>'

    def __repr__(self):
        return self.__str__()

    def merge(self, new):
        if self.origin_as != new.origin_as:
            if len(self.as_paths):
                self.origin_as = None
            else:
                self.origin_as = new.origin_as
        self.as_paths += new.as_paths
        # is_aggregable, etc. semantics...?

    def add_aspath(self, as_path):
        if self.origin_as != as_path[0]:
            if len(self.as_paths):
                self.origin_as = None
            else:
                self.origin_as = as_path[0]
        self.as_paths.append(as_path)


def process_table(infile, root_list):
    """Process the contents of the text-formatted routing table and form a
    prefix tree for later processing, storing the output in root_list which
    contains the prefix tree corresponding to each /8 in the IPv4 address space.

    The input text file is assumed to be in contiguous blocks organized by
    prefix to keep things efficient.

    Arguments
    infile -- a file-like object where each line is a routing table entry in
    PREFIX AS_PATH format

    """
    line_count = 0
    prefix_str = ""
    new_cidrprefix = None
    for line in infile:
        # TODO this needs to change to handle peers with same AS, different IP
        components = line.split()
        [prefix, prefix_len] = components[0].split('/')
        as_path = [extract_asn(asn) for asn in components[1:]]
        as_path.reverse()

        if prefix_str == components[0]:
            new_cidrprefix.add_aspath(as_path)
        else:
            prefix_str = components[0]
            # add old prefix to tree
            if new_cidrprefix:
                if new_cidrprefix.prefix_len == 8:
                    if root_list[new_cidrprefix.prefix >> 24] is None:
                        root_list[new_cidrprefix.prefix >> 24] = new_cidrprefix
                    else:
                        root_list[new_cidrprefix.prefix >> 24].merge(new_cidrprefix)
                elif new_cidrprefix.prefix_len > 8:
                    if root_list[new_cidrprefix.prefix >> 24] is None:
                        root_list[new_cidrprefix.prefix >> 24] = CidrPrefix(
                            new_cidrprefix.prefix & 0xFF000000, 8)
                    add_node_to_tree(root_list[new_cidrprefix.prefix >> 24],
                        new_cidrprefix)
                else:
                    print("error, prefix bigger than /8 !")
            # create new prefix
            new_cidrprefix = CidrPrefix(ipv4.dotquad_to_int(prefix),
                int(prefix_len), as_path, is_aggregable=True)

        line_count += 1
        if line_count % 1000 == 0:
            print line_count

def add_node_to_tree(root, new):
    """Add node new to the prefix tree rooted at root. Update all ancestor nodes
    traversed from root to the proper location of new.

    """
    cursor = root
    test_mask = 0x00800000

    for i in xrange(9, new.prefix_len+1):
        update_ancestor(cursor, new)
        if test_mask & new.prefix > 0:
            if cursor.ms_1 == None:
                if i == new.prefix_len:
                    cursor.ms_1 = new
                else:
                    cursor.ms_1 = CidrPrefix(
                        prefix=(cursor.prefix | test_mask), prefix_len=i)
            else:
                if i == new.prefix_len:
                    cursor.ms_1.merge(new)
            cursor = cursor.ms_1
        else:
            if cursor.ms_0 == None:
                if i == new.prefix_len:
                    cursor.ms_0 = new
                else:
                    cursor.ms_0 = CidrPrefix(prefix=cursor.prefix, prefix_len=i)
            else:
                if i == new.prefix_len:
                    cursor.ms_0.merge(new)
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
    if len(ancestor.as_paths) and len(descendant.as_paths):
        if ancestor.prefix_class == PREFIX_CLASSES.LONELY:
            ancestor.prefix_class = PREFIX_CLASSES.TOP
#            print(str(ancestor) + " is TOP")
        if as_paths_match(ancestor, descendant):
            descendant.prefix_class = PREFIX_CLASSES.DEAGG
#            print(str(descendant) + " is DEAGG")
            if ancestor.is_aggregable:
                ancestor.aggregable_more_specifics += 1
        else:
            descendant.prefix_class = PREFIX_CLASSES.DELEG
#            print(str(descendant) + " is DELEG")
            if ancestor.is_aggregable:
#                print(str(ancestor) + " is not aggregable")
                ancestor.is_aggregable = False
                ancestor.aggregable_more_specifics = 0

def as_paths_match(anc, des):
    """Check to see if the ancestor's AS_PATHs and the descendant's AS_PATHs are
    compatible for aggregation. Returns True if compatible, or False otherwise.
    We define compatibility as whether the fragment of each of descendant's
    AS_PATHs from the descendant's origin to the ancestor's origin are equal. If
    the ancestor is a multiple-origin prefix, this is not compatible.

    Example: (origin is the rightmost asn)

    10.0.0.0/8          3356 3 10
                        7018 3 10
    10.128.0.0/9        3356 3 10 30
                        26 7018 3 10 30
    10.128.128.0/16     3356 3 10 30
                        26 7018 50 30

    10/8 and 10.128/9 are aggregable because:
    - 10/8's (single) origin
        = AS10
    - path fragments from 10/8's origin to 10.128/9's origin
        = 10 30
        = 10 30
    - both paths are equal -- aggregable

    10/8 and 10.128.128/16 are NOT aggregable because:
    - 10/8's (single) origin
        = AS10
    - path fragments from 10/8's origin to 10.128.128/16's origin
        = 10 30
        = [] (AS10 NOT FOUND in 26 7018 50 30)
    - paths are not equal -- NOT aggregable

    TODO what about the crazy case of deaggregates corresponding 1-to-1 to each
    of the the ancestor's MOAS routes?

    """
    match = True
    if anc.origin_as:
        try:
            # .index(anc_origin)+1 to include anc_origin in path fragment
            #
            # all paths must be equal, so we'll use the first as our yardstick
            p = des.as_paths[0]
            check_path = deprepend_as_path(p[:p.index(anc.origin_as)])
            for p in des.as_paths[1:]:
                if check_path != deprepend_as_path(p[:p.index(anc.origin_as)]):
                    match = False
                    break
        except ValueError:
            match = False
    else:
#        print("error: ancestor is MOAS")
        match = False
    return match

def as_paths_match_origin(anc, des):
    match = True
    if anc.origin_as and des.origin_as:
        try:
            if des.as_paths[0].index(anc.origin_as) > 0:
                match = False
        except ValueError:
            match = False
    else:
        match = False
    return match

def as_paths_match_to_dfz(anc, des):
    match = True
    if anc.origin_as and des.origin_as:
        try:
            if des.as_paths[0].index(anc.origin_as) > 0:
                match = False
        except ValueError:
            match = False
        first_des_fragment = None
        for as_path in des.as_paths:
            as_path = deprepend_as_path(as_path)
            for i in xrange(len(as_path)):
                if as_path[i] in DFZ_ASNS:
                    first_des_fragment = as_path[:i]
                    break

        if first_des_fragment:
            print(ipv4.int_to_dotquad(des.prefix) + " First fragment: "
                + str(first_des_fragment))
        else:
            match = False

        print("descendants")
        for as_path in des.as_paths:
            as_path = deprepend_as_path(as_path)
            for i in xrange(len(as_path)):
                if as_path[i] in DFZ_ASNS:
                    print(as_path[:i])
                    #print(as_path)
                    if as_path[:i] != first_des_fragment:
                        match = False
                    break
        print("ancestors")
        for as_path in anc.as_paths:
            as_path = deprepend_as_path(as_path)
            for i in xrange(len(as_path)):
                if as_path[i] in DFZ_ASNS:
                    print(as_path[:i])
                    #print(as_path)
                    if as_path[:i] != first_des_fragment:
                        match = False
                    break
    else:
        match = False
    return match

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
    if prefix.origin_as:
        as_netsnow_dict[prefix.origin_as] = as_netsnow_dict.get(
            prefix.origin_as, 0) + 1
    elif len(prefix.as_paths): # MOAS
        for asn in set([as_path[0] for as_path in prefix.as_paths]):
            as_netsnow_dict[asn] = as_netsnow_dict.get(asn, 0) + 1
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
    tbl_pctgain = 100.0*float(tbl_netgain)/float(tbl_netsnow)
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
        pctgain = 100.0*float(netgain)/float(netsnow)
        print("{0:<8}{1:>8}    {2:>8}    {3:>8}    {4:>8.3}%".format(
            as_num, netsnow, netsaggr, netgain, pctgain))
        sum_netsnow += netsnow
        sum_netsaggr += netsaggr
        sum_netgain += netgain

    sum_pctgain = 100.0*float(sum_netgain)/float(sum_netsnow)
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

def plot_tree(rl, classa):
    import networkx as nx
    import matplotlib.pyplot as plt
    graph = nx.DiGraph()
    _plot_tree_helper(rl[classa], rl[classa], graph, 0, force=True)
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

    if len(node.as_paths):
        graph.add_node(node, shape='box', penwidth=2)
        if node.aggregable_more_specifics > 0:
            graph.node[node]['style'] = 'filled'
            graph.node[node]['fillcolor'] = 'palegreen'
        if node.prefix_class is PREFIX_CLASSES.LONELY:
            graph.node[node]['color'] = 'black'
        elif node.prefix_class is PREFIX_CLASSES.TOP:
            graph.node[node]['color'] = 'blue'
        elif node.prefix_class is PREFIX_CLASSES.DEAGG:
            graph.node[node]['color'] = 'green'
        elif node.prefix_class is PREFIX_CLASSES.DELEG:
            graph.node[node]['color'] = 'red'
#        else:
#            graph.node[node]['color'] = 'red'
        graph.node[node]['label'] = ' '.join([str(node),
            str(node.aggregable_more_specifics), str(node.origin_as), '\\n'])
        graph.node[node]['label'] += '\\n'.join(
            [str(ap) for ap in node.as_paths])
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