#!/usr/bin/env python2.6

DFZ_ASNS = [209, 701, 1239, 1299, 2828, 2914, 3356, 3549, 3561, 6453, 6461,
    7018]

PRIVATE_AS_START = 64512
PRIVATE_AS_END = 65551

def normalize_as_path(path):
    # find AS_CONFED_{SETS,SEQUENCES}
    path = remove_private_confed_paths(path)
    # remove AS_SETs and convert to ints
    norm_path = [extract_asn(e) for e in path]
    # remove private ASNs
    norm_path = [e for e in norm_path
        if e < PRIVATE_AS_START or e > PRIVATE_AS_END]
    norm_path = deprepend_as_path(norm_path)
    # TODO how to deal with 0s in AS_PATH?
    norm_path = deloop_as_path(norm_path)
    return norm_path


def remove_private_confed_paths(path):
    """Remove AS_CONFED_SEQUENCEs (65001 65002) and AS_CONFED_SETs [65001,65002]
    containing all private AS numbers before continuing. If the numbers aren't
    all private, these SETs/SEQUENCEs are left in, incluidng the syntax, which
    will throw a ValueError when extract_asn is run on them.

    """
    start_confed_seq = -1
    end_confed_seq = -1
    deletable_indices = []

    for i in xrange(len(path)):
        # check for private AS_CONFED_SET (i.e. '[65000,65001]')
        if -1 < path[i].find('[') < path[i].find(']'):
            if path[i].find('[') == 0 and path[i].find(']') == len(path[i])-1:
                components = path[i][1:-1].split(',')
                try:
                    if all((PRIVATE_AS_START <= int(c) <= PRIVATE_AS_END
                        for c in components)):
                        deletable_indices.append(i)
                except ValueError:
                    pass

        # check for private AS_CONFED_SEQ (i.e. '(65000 65001)')
        if path[i].find('(') > -1:
            start_confed_seq = i
        if path[i].find(')') > -1:
            end_confed_seq = i
        if -1 < start_confed_seq <= end_confed_seq:
            removable = True
            for j in xrange(start_confed_seq,end_confed_seq+1):
                as_str = path[j]
                if j == start_confed_seq:
                    as_str = as_str[1:]
                if j == end_confed_seq:
                    as_str = as_str[:-1]
                try:
                    if not (PRIVATE_AS_START <= int(as_str) <= PRIVATE_AS_END):
                        removable = False
                        break
                except ValueError:
                    removable = False
                    break
            if removable:
                deletable_indices += range(start_confed_seq, end_confed_seq+1)
            start_confed_seq = -1
            end_confed_seq = -1

    deletable_indices.sort(reverse=True)
    for index in deletable_indices:
        del path[index]
    return path


def extract_asn(s):
    """A helper function to extract AS numbers from AS_PATH string elements that
    may contain AS_SETs (denoted by '{ASN1, ASN2, ...}'). If the string does not
    contain an AS_SET or if the AS_SET contains only one AS number, the AS
    number is returned. If the AS_SET contains two or more ASNs, 0 is returned.
    If an unparsable AS_PATH element is passed, a ValueError will be raised.

    """
    try:
        s = s.strip()
    except AttributeError:
        # instead of TypeError, try and convert -- it may already be an int
        # if it's not an it, it will raise a TypeError anyway
        return int(s)

    if -1 < s.find('{') < s.find('}'):
        if s.find('{') == 0 and s.find('}') == len(s)-1:
            components = s[1:-1].split(',')
            if len(components) == 1:
                return int(components[0].strip())
            else:
                return 0
        else:
            raise ValueError
    else:
        return int(s)


def deprepend_as_path(path):
    """A helper function to remove AS_PATH prepending while maintaining the
    order of AS_PATH traversal. This is used to produce a canonical
    representation of each AS_PATH from a routing policy perspective (but not
    TE, BGP decision algorithm, etc. perspective)

    Example:

        deprepend_as_path([1, 1, 2, 3, 3, 4, 5, 5]) = [1, 2, 3, 4, 5]
        deprepend_as_path([1, 1, 2, 3, 3, 1, 1, 1, 2, 1]) = [1, 2, 3, 1, 2, 1]

    """
    current_as = None
    new_path = []
    for asn in path:
        if asn != current_as:
            current_as = asn
            new_path.append(asn)
    return new_path


def deloop_as_path(path):
    """A helper function to remove AS loops in the AS_PATH while maintaining the
    order of AS number traversal along the path.  This is used in part to
    produce a canonical representation of each AS_PATH from a routing policy
    perspective.

    This function borrows it's logic from CAIDA's straightenRV tool.

    Returns a loop-free version of the original path, or None if the loop cannot
    be resolved (multiple/overlapping loops).
    """
    asn_first_index = {}
    loop_start_index = None
    loop_end_index = None
    for i in xrange(len(path)):
        asn = path[i]
        if asn in asn_first_index:
            if not loop_start_index:
                loop_start_index = asn_first_index[asn]
            loop_end_index = i
        else:
            asn_first_index[asn] = i

    if loop_start_index:
        if path[loop_start_index] == path[loop_end_index]:
            # single loop detected -- replace loop with first AS in loop
            return path[:loop_start_index+1] + path[loop_end_index+1:]
        else:
            # multiple/overlapping loops
            return None
    else:
        return path

def path_to_string(as_path):
    return ' '.join((str(x) for x in as_path))

## OLD STUFF FROM AGGTREE.PY -- MAY EVENTUALLY BE DELETED
#
#def as_paths_match_to_parent_origin(anc, des):
#    """Check to see if the ancestor's AS_PATHs and the descendant's AS_PATHs are
#    compatible for aggregation. Returns True if compatible, or False otherwise.
#    We define compatibility as whether the fragment of each of descendant's
#    AS_PATHs from the descendant's origin to the ancestor's origin are equal. If
#    the ancestor is a multiple-origin prefix, this is not compatible.
#
#    Example: (origin is the rightmost asn)
#
#    10.0.0.0/8          3356 3 10
#                        7018 3 10
#    10.128.0.0/9        3356 3 10 30
#                        26 7018 3 10 30
#    10.128.128.0/16     3356 3 10 30
#                        26 7018 50 30
#
#    10/8 and 10.128/9 are aggregable because:
#    - 10/8's (single) origin
#        = AS10
#    - path fragments from 10/8's origin to 10.128/9's origin
#        = 10 30
#        = 10 30
#    - both paths are equal -- aggregable
#
#    10/8 and 10.128.128/16 are NOT aggregable because:
#    - 10/8's (single) origin
#        = AS10
#    - path fragments from 10/8's origin to 10.128.128/16's origin
#        = 10 30
#        = [] (AS10 NOT FOUND in 26 7018 50 30)
#    - paths are not equal -- NOT aggregable
#
#    TODO what about the crazy case of deaggregates corresponding 1-to-1 to each
#    of the the ancestor's MOAS routes?
#
#    """
#    match = True
#    if anc.origin_as:
#        try:
#            # .index(anc_origin)+1 to include anc_origin in path fragment
#            #
#            # all paths must be equal, so we'll use the first as our yardstick
#            p = des.as_paths[0]
#            check_path = deprepend_as_path(p[:p.index(anc.origin_as)])
#            for p in des.as_paths[1:]:
#                if check_path != deprepend_as_path(p[:p.index(anc.origin_as)]):
#                    match = False
#                    break
#        except ValueError:
#            match = False
#    else:
##        print("error: ancestor is MOAS")
#        match = False
#    return match
#
#def as_paths_match_origin(anc, des):
#    match = True
#    if anc.origin_as and des.origin_as:
#        try:
#            if des.as_paths[0].index(anc.origin_as) > 0:
#                match = False
#        except ValueError:
#            match = False
#    else:
#        match = False
#    return match
#
#def as_paths_match_to_dfz(anc, des):
#    match = True
#    if anc.origin_as and des.origin_as:
#        try:
#            if des.as_paths[0].index(anc.origin_as) > 0:
#                match = False
#        except ValueError:
#            match = False
#        first_des_fragment = None
#        for as_path in des.as_paths:
#            as_path = deprepend_as_path(as_path)
#            for i in xrange(len(as_path)):
#                if as_path[i] in DFZ_ASNS:
#                    first_des_fragment = as_path[:i]
#                    break
#
#        if first_des_fragment:
#            print(ipv4.int_to_dotquad(des.prefix) + " First fragment: "
#                + str(first_des_fragment))
#        else:
#            match = False
#
#        print("descendants")
#        for as_path in des.as_paths:
#            as_path = deprepend_as_path(as_path)
#            for i in xrange(len(as_path)):
#                if as_path[i] in DFZ_ASNS:
#                    print(as_path[:i])
#                    #print(as_path)
#                    if as_path[:i] != first_des_fragment:
#                        match = False
#                    break
#        print("ancestors")
#        for as_path in anc.as_paths:
#            as_path = deprepend_as_path(as_path)
#            for i in xrange(len(as_path)):
#                if as_path[i] in DFZ_ASNS:
#                    print(as_path[:i])
#                    #print(as_path)
#                    if as_path[:i] != first_des_fragment:
#                        match = False
#                    break
#    else:
#        match = False
#    return match
