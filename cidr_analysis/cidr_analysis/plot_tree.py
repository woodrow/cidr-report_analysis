#!/usr/bin/env python2.6

"""Functions used to generate graphviz .dot files of the prefix trees for
visualization of aggregation.


"""

import os
import datetime

from prefix_classes import PREFIX_CLASSES

def plot_tree(root, plot_dir, rib_name=''):
    peer_set = set()
    as_map = {}
    nowstr = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    find_all_peers(root, peer_set, as_map)
    for peer in peer_set:
        dotfile = open(os.path.join(plot_dir,'plot-' + str(peer) +'.dot'), 'w')
        dotfile.write('strict digraph {\n'
            '\tordering=out;\n')
        dotfile.write('\tlabel="' + '  /  '.join([
            'AS ' + str(as_map[peer]),
            'plot-' + str(peer) +'.dot',
            rib_name,
            nowstr]) + '";\n')
        dotfile.write('\tfontname="Bitstream Vera Sans";\n'
            '\tfontsize=36;\n'
            '\tlabelloc=t;\n'
            '\tlabeljust=l;\n')
        _plot_tree_helper(root, root, peer, dotfile, 0, force=True)
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


def _plot_tree_helper(node, parent_node, peer, dotfile, deep, force=False):
    if peer in node.attrs:
        node_label = ' '.join([str(node),
            '(-' + str(node.attrs[peer].agg_children) + ', +'  + str(node.attrs[peer].adv_children) + ')',
            '\\n', str(node.attrs[peer].as_path)])
        node_other = 'penwidth=2, shape=box, style=filled, fontname="Bitstream Vera Sans"'
        if node.attrs[peer].is_advertised:
            node_other += ', fillcolor=palegreen'
        else:
            node_other += ', fillcolor=grey'
        if node.attrs[peer].prefix_class is PREFIX_CLASSES.LONELY:
            node_other += ', color=black'
        elif node.attrs[peer].prefix_class is PREFIX_CLASSES.TOP:
            node_other += ', color=blue3'
        elif node.attrs[peer].prefix_class is PREFIX_CLASSES.DEAGG:
            node_other += ', color=darkgreen'
        elif node.attrs[peer].prefix_class is PREFIX_CLASSES.DELEG:
            node_other += ', color=firebrick'
        else:
            node_other += ', color=firebrick'
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
        child = _plot_tree_helper(node.ms_0, node, peer, dotfile, deep+1)
        if child:
            dot_str += '\n\t"' + str(node) + '" -> "' + str(child) + '";'
    if node.ms_1:
        child = _plot_tree_helper(node.ms_1, node, peer, dotfile, deep+1)
        if child:
            dot_str += '\n\t"' + str(node) + '" -> "' + str(child) + '";'

    dotfile.write('\t' + dot_str + '\n')

    return node