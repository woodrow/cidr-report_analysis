#!/usr/bin/env python2.6

from cidr_analysis import aspath
import os

def postprocess_rib(rib_filename, norm_filename, peers_filename,
    ppapp_filename, include_peer_ip):
    # ppapp and ppp are keyed on peer_ip, or peer asn if there is no peer_ip
    ppapp = {}  # prefixes per as, per peer
    ppp = {}  # prefixes per peer
    peer_asns = {}

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
        raw_as_path = components[as_start_index:]
        raw_as_path.reverse()
        norm_path = aspath.normalize_as_path(raw_as_path)

        if norm_path:
            if include_peer_ip:
                outfile.write("{0:<18} {1:<15} {2}\n".format(
                    '/'.join([prefix, prefix_len]), peer_ip,
                    aspath.path_to_string(norm_path)))
                try:
                    ppapp.setdefault(peer_ip,{})[norm_path[0]] += 1
                    ppp[peer_ip] += 1
                except KeyError:
                    ppapp.setdefault(peer_ip,{}).setdefault(norm_path[0], 1)
                    ppp.setdefault(peer_ip,1)
                if peer_ip not in peer_asns:
                    peer_asns[peer_ip] = norm_path[-1]
            else:
                outfile.write("{0:<18} {1}\n".format(
                    '/'.join([prefix, prefix_len]),
                    aspath.path_to_string(norm_path)))
                try:
                    ppapp.setdefault(norm_path[-1],{})[norm_path[0]] += 1
                    ppp[norm_path[-1]] += 1
                except KeyError:
                    ppapp.setdefault(norm_path[-1],{}).setdefault(
                        norm_path[0], 1)
                    ppp.setdefault(norm_path[-1],1)
        else:
            print("dropping line due to invalid AS_PATH:\n  {0}".format(line))
    outfile.close()
    f.close()

    ppapp_file = open(ppapp_filename,'w')
    peers_file = open(peers_filename,'w')
    if include_peer_ip:
        #   ppapp_file.write("# prefix_count origin_as peer_as peer_ip\n")
        #   peers_file.write("# prefix_count peer_as peer_ip\n")
        for peer_ip in ppapp:
            for asn in ppapp[peer_ip]:
                ppapp_file.write('{0:>8} {1:>10} {2:>5} {3:<15}\n'.format(
                    ppapp[peer_ip][asn], asn, peer_asns[peer_ip], peer_ip))
        for peer_ip in ppp:
            peers_file.write('{0:>8} {1:>5} {2:<15}\n'.format(
                ppp[peer_ip], peer_asns[peer_ip], peer_ip))
    else:
        #ppapp_file.write("# prefix_count origin_as peer_as\n")
        #peers_file.write("# prefix_count peer_as\n")
        for peer_asn in ppapp:
            for asn in ppapp[peer_asn]:
                ppapp_file.write('{0:>8} {1:>10} {2:>10}\n'.format(
                    ppapp[peer_asn][asn], asn, peer_asn))
        for peer_asn in ppp:
            peers_file.write('{0:>8} {1:>5}\n'.format(
                ppp[peer_asn], peer_asn))
    ppapp_file.close()
    peers_file.close()

def process_txtrib(full_path, include_peer_ip=True):
    dir_name = os.path.dirname(full_path)
    base_name = '.'.join(os.path.basename(full_path).split('.')[:-1])
    full_name = os.path.join(dir_name, base_name)

    # filenames
    log_name = full_name + '.neighbors_log'
    txt_name = full_name + '.txt'
    normrib_name = full_name + '.normrib'
    peers_name = full_name + '.peers'
    ppapp_name = full_name + '.ppapp' #ppapp = prefixes per as, per peer

    print("Postprocessing RIB and generating .normrib, .peers, and .ppapp "
        "files.")
    postprocess_rib(txt_name, normrib_name, peers_name, ppapp_name,
        include_peer_ip)
    # TODO check to see that the files txt_name and normrib_name are rougly
    #      similar in size such that there wasn't a big error

    print("Sorting RIB by prefix first octet.")
    os.system(
        'sort -s -n -k 1,1 -t . {0} > {0}.sorted; mv {0}.sorted {0}'.format(
        normrib_name))
    print("Sorting .peers file.")
    os.system(
        'sort -r -n -k 1,1 {0} > {0}.sorted; mv {0}.sorted {0}'.format(
        peers_name))
    print("Sorting .ppapp file.")
    os.system(
        'sort -n -k 2,2 -k 3,3 {0} > {0}.sorted; mv {0}.sorted {0}'.format(
        ppapp_name))
    # TODO check for outliers in .peers and/or .ppapp files?
