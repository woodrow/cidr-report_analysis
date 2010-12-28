#!/usr/bin/env python2.6

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

def process_txtrib(full_path, include_peer_ip=False):
    dir_name = os.path.dirname(full_path)
    base_name = '.'.join(os.path.basename(full_path).split('.')[:-1])
    full_name = os.path.join(dir_name, base_name)

    # filenames
    log_name = full_name + '.neighbors_log'
    txt_name = full_name + '.txt'
    normrib_name = full_name + '.normrib'
    peers_name = full_name + '.peers'
    ppapp_name = full_name + '.ppapp' #ppapp = prefixes per as, per peer

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
