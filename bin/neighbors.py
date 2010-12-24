#!/usr/bin/env python2.6

import os
import sys
import re

BGPDUMP_PATH = os.path.realpath(
    '../libbgpdump/libbgpdump-1.4.99.13/simpledump')
STRAIGHTENRV_PATH = os.path.realpath(
    '../rv2atoms-0.5/bin/straightenRV')

def generate_files(full_path, include_peer_ip=False):
    dir_name = os.path.dirname(full_path)
    base_name = '.'.join(os.path.basename(full_path).split('.')[:-1])
    full_name = os.path.join(dir_name, base_name)

    # filenames
    log_name = full_name + '.neighbors_log'
    txt_name = full_name + '.txt'
    normrib_name = full_name + '.normrib'
    peers_name = full_name + '.peers'
    ppapp_name = full_name + '.ppapp' #ppapp = prefixes per as, per peer

    # generate routing table txt file
    print("Generating .txt routing table.")
    if full_name.find('oix-full') == -1:
        # new table
        # TODO: capture debugging output
        os.system(' '.join([BGPDUMP_PATH, '-p' if include_peer_ip else '',
            full_path, txt_name]))
    else:
        # old table
        # TODO should this be d = 0?
        os.system(' '.join([STRAIGHTENRV_PATH, '-m all -d 1', full_path]))
        # delete unnecessary files
        # unzip fullname.full.gz
        # extract prefix, peer ip, and AS_PATH
        # -OR-
        # hack straightenrv to output prefix, peer ip, AS_PATH directly!!


    # postprocess routing table txt file
    # TODO: capture debugging output
    postprocess_rib(txt_name, normrib_name, include_peer_ip)
    # TODO check to see that their sizes are rougly similar?

    if include_peer_ip:
        args_peers = ' '.join(["awk '{print \"(\" $NF, $2 \")\"}'",
            normrib_name, '| sort | uniq -c | sort -r -n >', peers_name])
        args_ppapp = ' '.join(["awk '{print \"(\" $NF, $2 \")\", $3}'",
            normrib_name, '| sort | uniq -c | sort -n -k 4 -s >', ppapp_name])
    else:
        args_peers = ' '.join(["awk '{print $NF}'",
            normrib_name, '| sort | uniq -c | sort -r -n >', peers_name])
        args_ppapp = ' '.join(["awk '{print $NF, $2}'",
            normrib_name, '| sort | uniq -c | sort -n -k 3 -s >', ppapp_name])

    print("Generating .peers file.")
    os.system(args_peers)
    print("Generating .ppapp file.")
    os.system(args_ppapp)

def postprocess_rib(rib_filename, norm_filename, include_peer_ip):
    f = open(rib_filename, 'r')
    outfile = open(norm_filename, 'w')
    for line in f:
        components = line.split()
        [prefix, prefix_len] = components[0].split('/')
        if include_peer_ip:
            peer_ip = components[1]
            as_start_index = 2
        else:
            peer_ip = None
            as_start_index = 1
            as_path = components[as_start_index:]
        as_path.reverse()
        norm_path = normalize_as_path(as_path)
        if norm_path:
            if include_peer_ip:
                outfile.write("{0}/{1} {2} {3}\n".format(
                    prefix, prefix_len, peer_ip, ' '.join(norm_path)))
            else:
                outfile.write("{0}/{1} {2}\n".format(
                    prefix, prefix_len, ' '.join(norm_path)))
        else:
            print("dropping line due to invalid AS_PATH:\n  {0}".format(line))
    outfile.close()
    f.close()

def normalize_as_path(path):
    new_path = [extract_asn(e) for e in path] # remove AS_SETs
    new_path = [e for e in path if e < 64512 or e > 65551] # remove private
    new_path = deprepend_as_path(new_path)
    new_path = deloop_as_path(new_path)
    return new_path

def extract_asn(s):
    """A helper function to extract AS numbers from AS_PATH string elements that
    may contain AS_SETs (denoted by '{ASN1, ASN2, ...}'). If the string does not
    contain an AS_SET or if the AS_SET contains only one AS number, the AS
    number is returned. If the AS_SET contains two or more ASNs, 0 is returned.

    """
    s = s.strip()
    #TODO should I worrry about AS_CONFED_SET and AS_CONFED_SEQ?
    if s.find('{') > -1:
        components = s[1:-1].split(',')
        if len(components) == 1:
            return int(components[0])
        else:
            return 0
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

def usage():
    print(' '.join(["Usage:", sys.argv[0], '[-p] MRT_RIB_FILE']))
    print("""Produces intermediate text-based routing table (.txt) and peer
table (.peer) based on supplied MRT_RIB_FILE.

Optional flag -p will include peer ip addresses to determine unique neighbors.
""")

def main():
    include_peer_ip = False
    if 1 < len(sys.argv) < 4:
        if len(sys.argv) == 2:
            full_path = os.path.realpath(sys.argv[1])
        else:
            if sys.argv[1] == '-p':
                include_peer_ip = True
            else:
                usage()
                exit()
            full_path = os.path.realpath(sys.argv[2])
        generate_files(full_path, include_peer_ip)
    else:
        usage()

if __name__ == '__main__':
    main()
