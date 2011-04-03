import multiprocessing
import Queue
import os.path
import datetime
import re
import subprocess

# same-module imports
import aspath
import utils


class PrefixOrigin(object):
    def __init__(self, origin_as, date_effective, weeks_seen):
        self.origin_as = origin_as
        self.date_effective = date_effective
        self.weeks_seen = weeks_seen


def get_peerid_factory(peermap, peermap_lock, local_peermap):
    def get_peerid(peer_as, peer_ip):
        peer_tuple = (peer_as, peer_ip)
        try:
            return local_peermap[peer_tuple]
        except KeyError:
            peermap_lock.acquire()
            assert len(peermap)+1 not in peermap.values()  # extra precaution
            peer_id = peermap.setdefault(peer_tuple, len(peermap)+1)
            peermap_lock.release()
            local_peermap[peer_tuple] = peer_id
            return peer_id
    return get_peerid


def process_txtrib_worker(txtrib_queue, peermap, peermap_lock, stdout_lock):
    """Assume incoming txtrib file is sorted before processing such that
    prefixes are in contiguous blocks."""
    local_peermap = {}
    get_peerid = get_peerid_factory(peermap, peermap_lock, local_peermap)

    while True:  # process txtrib_queue for work until empty
        debug_output = []
        try:
            txtrib_path = txtrib_queue.get_nowait()
        except Queue.Empty:
            return

        # generate filenames
        dir_name = os.path.dirname(txtrib_path)
        base_name = '.'.join(os.path.basename(txtrib_path).split('.')[:-1])
        full_path = os.path.join(dir_name, base_name)
        normrib_path = full_path + '.normrib'
        peers_path = full_path + '.peers'
        ppapp_path = full_path + '.ppapp' #ppapp = prefixes per as, per peer
        peersum_path = full_path + '.peersum'
        origins_path = full_path + '.origins'

        # open files
        txtrib_file = open(txtrib_path)
        normrib_file = open(normrib_path, 'w')
        origins_file = open(origins_path, 'w')

        # insert front matter
        origins_file.write(
            "# generated on {0} UTC\n".format(datetime.datetime.utcnow()))
        origins_file.write("# prefix,peerid,origin_as,ordinal_date\n")

        # ppapp and ppp are keyed on peer_ip, or peer asn if there is no peer_ip
        ppapp = {}  # prefixes per as per peer, keyed on peer_ip and origin_as
        ppp = {}  # prefixes per peer, keyed on peer_ip
        peer_asns = {} # peer_ip -> peer_asn map
        single_aspath_lines = Queue.Queue()
        current_prefix = None
        prefix_origin_map = {} # prefix -> set(origin_as)
        prefix_origin_set = set()
        save_prefix_origin_set = False

        date_sort = utils.extract_rib_date(txtrib_path).toordinal()
        date_str = utils.extract_rib_date(txtrib_path).strftime('%Y-%m-%d')

        debug_output.append((
            "Postprocessing RIB and generating .normrib, "
            ".peers, .ppapp, .peersum, and .origins files for {0}."
            ).format(base_name))

        for line in txtrib_file:
            components = line.split()
            prefix = components[0]
            peer_ip = components[1]
            raw_as_path = components[2:]

            if prefix != current_prefix:
                if save_prefix_origin_set and prefix_origin_set:
                    prefix_origin_map[current_prefix] = prefix_origin_set
                current_prefix = prefix
                prefix_origin_set = set()
                save_prefix_origin_set = False

            if len(raw_as_path) == 1:
                single_aspath_lines.put_nowait(line)
                save_prefix_origin_set = True
                continue

            try:
                # TODO capture notes/output from normalize_as_path
                norm_path = aspath.normalize_as_path(raw_as_path)
                if norm_path:
                    norm_path.reverse()
            except (AttributeError, LookupError, ValueError):
                norm_path = None

            if norm_path:
                normrib_file.write(
                    "{0:<18} {1:<15} {2}\n".format(prefix, peer_ip,
                    aspath.path_to_string(norm_path)))
                prefix_origin_set.add(norm_path[0])
                origins_file.write(
                    "{0},{1},{2},{3}\n".format(prefix,
                    get_peerid(norm_path[-1], peer_ip),
                    norm_path[0], date_sort))
                try:
                    ppapp.setdefault(peer_ip, {})[norm_path[0]] += 1
                    ppp[peer_ip] += 1
                except KeyError:
                    ppapp.setdefault(peer_ip, {}).setdefault(norm_path[0], 1)
                    ppp.setdefault(peer_ip, 1)
                if peer_ip not in peer_asns:
                    peer_asns[peer_ip] = norm_path[-1]
            else:
                debug_output.append(
                    "INVALID AS_PATH: dropping '{0}'".format(line.strip()))

        # Handle remaining single ASN as_paths
        debug_output.append(
            "Handling {0} single AS_PATHs".format(single_aspath_lines.qsize()))
        while not single_aspath_lines.empty():
            line = single_aspath_lines.get_nowait()
            [prefix, peer_ip, single_asn] = line.split()
            if single_asn == '-':
                is_null = True
                raw_as_path = []
            else:
                is_null = False
                single_asn = int(single_asn)
                raw_as_path = [single_asn]

            origin_set = prefix_origin_map.get(prefix)
            if origin_set:
                if single_asn in origin_set:  # tie-breaker chooses same AS
                    origin_as = single_asn
                else:
                    origin_as = min(origin_set)
            else:
                origin_as = None
            peer_as = peer_asns.get(peer_ip)

            if is_null:
                if peer_as:
                    raw_as_path.append(peer_as)
                if origin_as:
                    raw_as_path.append(origin_as)
            elif single_asn == peer_as:
            # the single_asn is the peer ASN
                if origin_as:
                    raw_as_path.append(origin_as)
            elif single_asn == origin_as:
            # the single_asn is the origin ASN
                if peer_as:
                    raw_as_path.insert(0, peer_as)

            if len(raw_as_path) <= 1 and single_asn != peer_as:
                debug_output.append(
                    "AMBIGUOUS AS_PATH: dropping '{0}'".format(line.strip()))
            else:
                raw_as_path = [str(x) for x in raw_as_path]
                ##### DUPLICATE FROM ABOVE -- FIND A BETTER WAY ################
                try:
                    # TODO capture notes/output from normalize_as_path
                    norm_path = aspath.normalize_as_path(raw_as_path)
                    if norm_path:
                        norm_path.reverse()
                except (AttributeError, LookupError, ValueError):
                    norm_path = None

                if norm_path:
                    normrib_file.write(
                        "{0:<18} {1:<15} {2}\n".format(prefix, peer_ip,
                        aspath.path_to_string(norm_path)))
                    origins_file.write(
                        "{0},{1},{2},{3}\n".format(prefix,
                        get_peerid(norm_path[-1], peer_ip),
                        norm_path[0], date_sort))
                    try:
                        ppapp.setdefault(peer_ip, {})[norm_path[0]] += 1
                        ppp[peer_ip] += 1
                    except KeyError:
                        ppapp.setdefault(peer_ip, {}).setdefault(
                            norm_path[0], 1)
                        ppp.setdefault(peer_ip, 1)
                    if peer_ip not in peer_asns:
                        peer_asns[peer_ip] = norm_path[-1]
                else:
                    debug_output.append(
                        "INVALID AS_PATH: dropping '{0}'".format(line.strip()))
                ##### END DUPLICATE FROM ABOVE #################################

        txtrib_file.close()
        normrib_file.close()
        origins_file.close()

        ppapp_file = open(ppapp_path,'w')
        ppapp_file.write("# prefix_count origin_as peer_as peer_ip\n")
        peersum_file = open(peersum_path, 'w')
        peersum_file.write(
            "# generated on {0} UTC\n".format(datetime.datetime.utcnow()))
        peersum_file.write("# date,origin_as,peerid,ppapp\n")
        for peer_ip in ppapp:
            for origin_as in ppapp[peer_ip]:
                ppapp_file.write(
                    '{0:>8} {1:>10} {2:>5} {3:<15}\n'.format(
                    ppapp[peer_ip][origin_as], origin_as,
                    peer_asns[peer_ip], peer_ip))
                # TODO include notes
                peerid = get_peerid(peer_asns[peer_ip], peer_ip)
                peersum_file.write("{0},{1},{2},{3}\n".format(
                    date_str, origin_as, peerid, ppapp[peer_ip][origin_as]))
        ppapp_file.close()
        peersum_file.close()

        peers_file = open(peers_path,'w')
        peers_file.write("# prefix_count peer_as peer_ip\n")
        for peer_ip in ppp:
            peers_file.write('{0:>8} {1:>5} {2:<15}\n'.format(
                ppp[peer_ip], peer_asns[peer_ip], peer_ip))
        peers_file.close()

        subprocess.check_call((
            'sort -n -k 1,1 -o {0}.sorted {0};'
            'mv {0}.sorted {0}'
            ).format(normrib_path), shell=True)
        subprocess.check_call((
            'sort -r -n -k 1,1 -o {0}.sorted {0};'
            'mv {0}.sorted {0}'
            ).format(peers_path), shell=True)
        subprocess.check_call((
            'sort -n -k 2,2 -o {0}.sorted {0};'
            'mv {0}.sorted {0}'
            ).format(ppapp_path), shell=True)

        stdout_lock.acquire()
        print("\n".join(debug_output))
        stdout_lock.release()


def process_txtrib_mp(txtrib_files, num_processes, output_dir):
    txtrib_queue = multiprocessing.Queue()
    for txtrib_file in txtrib_files:
        txtrib_queue.put_nowait(os.path.abspath(txtrib_file))

    manager = multiprocessing.Manager()
    peermap = manager.dict()
    peermap_lock = multiprocessing.Lock()
    stdout_lock = multiprocessing.Lock()

    workers = [
        multiprocessing.Process(
            target=process_txtrib_worker, args=(txtrib_queue, peermap,
            peermap_lock, stdout_lock))
        for _ in xrange(num_processes)]
    for process in workers:
        process.start()
    for process in workers:
        process.join()

    if peermap:
        peer_file = open(os.path.join(output_dir, 'peers.csv'), 'w')
        peer_file.write(
            "# generated on {0} UTC\n".format(datetime.datetime.utcnow()))
        peer_file.write("# peer_id,peer_as,peer_ip\n")
        for peer in peermap.keys():
            peer_id = peermap[peer]
            peer_file.write("{0},{1[0]},{1[1]}\n".format(peer_id, peer))
        peer_file.close()

    # get list of filenames
    # sort by (apparent) date in filename
    # divide by number of workers and insert in lists accordingly
    # if db:
    #   maintain a Manager that keeps the master peer-int mapping dict, which is
    #   cached in each process instance
    # RUN SUBPROCESSES
    # if db:
    #   output peers.csv (peer-int mapping dict)
    #   stitch together prefix_history pickles, and output prefix_origins.csv
    # --------------------
    # FOR EACH process:
    #     output normrib
    #     if not db:
    #       output peers
    #       output ppapp
    #     else:
    #       maintain local cached copy of peer-int mapping dict
    #       output peer_summaries.csv
    #           >> be sure to keep notes of every "as-set originated route"
    #       output prefix_history pickle
    #           >> include start and end of date range for stitching purposes
    #           >> think about what to do about
