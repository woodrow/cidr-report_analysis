#!/usr/bin/env python2.6

"""Functions used to generate graphviz .dot files of the prefix trees for
visualization of aggregation.


"""

import os
import datetime

from prefix_classes import PREFIX_CLASSES

def plot_tree(root, plot_dir, rib_name='', origin_set=None):
    peer_set = set()
    as_map = {}
    nowstr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    find_all_peers(root, peer_set, as_map)
    for peer in peer_set:
        dotfile = open(os.path.join(plot_dir,'plot-' + str(peer) +'.dot'), 'w')
        dotfile.write('strict digraph {\n'
            '\tordering=out;\n')
        dotfile.write('\tlabel="' + '  /  '.join([
            "origins=" + str(origin_set) if origin_set else "[all]",
            'AS ' + str(as_map[peer]),
            'plot-' + str(peer) +'.dot',
            rib_name,
            nowstr]) + '";\n')
        dotfile.write('\tfontname="Bitstream Vera Sans";\n'
            '\tfontsize=36;\n'
            '\tlabelloc=t;\n'
            '\tlabeljust=l;\n')
        _plot_tree_helper(root, root, peer, dotfile, origin_set, force=True)
        dotfile.write('}')
        dotfile.close()
    # finally, print one for the whole tree:
    dotfile = open(os.path.join(plot_dir,'plot-routeviews.dot'), 'w')
    dotfile.write('strict digraph {\n'
        '\tordering=out;\n')
    dotfile.write('\tlabel="' + '  /  '.join([
        str(origin_set) if origin_set else "[all origins]",
        'AS ' + str(6447) + ' (Routeviews Aggregate)',
        'plot-routeviews.dot',
        rib_name,
        nowstr]) + '";\n')
    dotfile.write('\tfontname="Bitstream Vera Sans";\n'
        '\tfontsize=36;\n'
        '\tlabelloc=t;\n'
        '\tlabeljust=l;\n')
    _plot_tree_helper(root, root, None, dotfile, origin_set, force=True)
    dotfile.write('}')
    dotfile.close()


def find_all_peers(root, peer_set, as_map):
    for k in root.attrs:
        peer_set.add(k)
        as_map[k] = root.attrs[k].as_path[-1]
    if root.ms_0:
        find_all_peers(root.ms_0, peer_set, as_map)
    if root.ms_1:
        find_all_peers(root.ms_1, peer_set, as_map)


def _plot_tree_helper(node, parent_node, peer, dotfile, origin_set=None,
    force=False, deep=0):
    if not peer:
        node_label = ' '.join([str(node),
            '(-' + str(node.agg_children) + ', +'
            + str(node.adv_children) + ')',
            '\\n', str(node.origin_as)])
        node_other = ('penwidth=2, shape=box, style=filled, '
            'fontname="Bitstream Vera Sans"')
        if node.is_advertised:
            node_other += ', fillcolor=palegreen'
        else:
            node_other += ', fillcolor=grey'
        if node.attrs and not node.is_intable:
            node_other += ', color=goldenrod'
        elif not node.attrs:
            node_label = ''
            node_other = 'shape=point'
    elif peer in node.attrs:
        if (not origin_set) or (node.attrs[peer].as_path[0] in origin_set):
            node_label = ' '.join([str(node),
                '(-' + str(node.attrs[peer].agg_children) + ', +'
                + str(node.attrs[peer].adv_children) + ')',
                '\\n', str(node.attrs[peer].as_path)])
            node_other = ('penwidth=2, shape=box, style=filled, '
                'fontname="Bitstream Vera Sans"')
            if node.attrs[peer].is_advertised:
                node_other += ', fillcolor=palegreen'
            else:
                node_other += ', fillcolor=grey'
            if not node.attrs[peer].is_intable:
                node_other += ', color=goldenrod'
            elif node.attrs[peer].prefix_class is PREFIX_CLASSES.LONELY:
                node_other += ', color=black'
            elif node.attrs[peer].prefix_class is PREFIX_CLASSES.TOP:
                node_other += ', color=blue3'
            elif node.attrs[peer].prefix_class is PREFIX_CLASSES.DEAGG:
                node_other += ', color=darkgreen'
            elif node.attrs[peer].prefix_class is PREFIX_CLASSES.DELEG:
                node_other += ', color=firebrick'
            else:
                node_other += ', color=firebrick'
        else:
            node_label = ''
            node_other = 'shape=point'
    elif force:
        node_label = str(node)
        node_other = 'penwidth=2, shape=box, style=filled, color=grey'
    else:
        node_label = ''
        node_other = 'shape=point'
    node_label = '"' + node_label + '"'
    node_name = '"' + str(node) + '"'

    dot_str = ''.join([node_name, ' [label=', node_label, ', ',
        node_other, '];'])

    if node.ms_0:
        child = _plot_tree_helper(node.ms_0, node, peer, dotfile, origin_set,
            deep=deep+1)
        if child:
            dot_str += '\n\t"' + str(node) + '" -> "' + str(child) + '";'
    if node.ms_1:
        child = _plot_tree_helper(node.ms_1, node, peer, dotfile, origin_set,
            deep=deep+1)
        if child:
            dot_str += '\n\t"' + str(node) + '" -> "' + str(child) + '";'

    dotfile.write('\t' + dot_str + '\n')

    return node