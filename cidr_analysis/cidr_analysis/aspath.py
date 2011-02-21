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
    number is returned. If the AS_SET contains two or more ASNs, -1 is returned.
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
                return -1  # MAGIC collapsed AS_SET number (p.95 of notebook)
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
