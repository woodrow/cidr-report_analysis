from multiprocessing import Process, Manager
import sys
import os.path
from collections import namedtuple
import datetime
import re
import math
import aspath
import pickle
import subprocess

class PrefixOrigin(object):
    def __init__(self, origin_as, date_effective, weeks_seen):
#        self.prefix = prefix
#        self.peer_id = peer_id
        self.origin_as = origin_as
        self.date_effective = date_effective
        self.weeks_seen = weeks_seen


def extract_rib_date(s):
    s = os.path.basename(s)
    try:
        return datetime.datetime.strptime(
            re.search('(\d{4}\-\d{2}\-\d{2})', s).groups()[0],
            '%Y-%m-%d').date()
    except AttributeError:
        return datetime.datetime.strptime(
            re.search('(\d{8})', s).groups()[0], '%Y%m%d').date()


def get_peerid_factory(master_peer_map, local_peer_map):
    def get_peerid(peer_as, peer_ip):
        peer_tuple = (peer_as, peer_ip)
        try:
            return local_peer_map[peer_tuple]
        except KeyError:
            peer_id = master_peer_map.setdefault(peer_tuple,
                len(master_peer_map)+1)
            local_peer_map[peer_tuple] = peer_id
            return peer_id
    return get_peerid


def add_prefix_to_history(history_map, peer_id, prefix, origin_as, date,
    raw_as_path=None, norm_as_path=None):
    prefix_map = history_map.setdefault(prefix, {})
    hist_list = prefix_map.setdefault(peer_id, [])
    if hist_list:
        numweeks = (date - hist_list[-1].date).days//7
        hist_list[-1].weeks_seen += '0'*(
                len(hist_list[-1].weeks_seen) - weeks_seen - 1)
    if not hist_list or hist_list[-1].origin_as != origin_as:
        hist_list.append(PrefixOrigin(origin_as,
#            aspath.path_to_string(raw_as_path),
#            aspath.path_to_string(norm_as_path),
            date, '1'))
    else:
        hist_list[-1].weeks_seen += '1'


def process_txtrib_worker(txtrib_paths, output_dir, master_peer_map, use_db):
    peer_map = {}
    if use_db and txtrib_paths:
        get_peerid = get_peerid_factory(master_peer_map, peer_map)

        peersum_path = os.path.join(output_dir,
            'peer_summaries.{0}.csv'.format(os.getpid()))
        peersum_file = open(peersum_path, 'w')
        peersum_file.write(
            "# generated on {0} UTC\n".format(datetime.datetime.utcnow()))
        peersum_file.write("# date,origin_as,peerid,ppapp\n")

        origins_path = os.path.join(output_dir,
            'prefix_origins.{0}.csv'.format(os.getpid()))
        origins_file = open(origins_path, 'w')
        origins_file.write(
            "# generated on {0} UTC\n".format(datetime.datetime.utcnow()))
        origins_file.write("# prefix,peerid,origin_as,sortdate,strdate\n")

    for txtrib_path in txtrib_paths:
        # filenames
        dir_name = os.path.dirname(txtrib_path)
        base_name = '.'.join(os.path.basename(txtrib_path).split('.')[:-1])
        full_path = os.path.join(dir_name, base_name)
        normrib_path = full_path + '.normrib'
        peers_path = full_path + '.peers'
        ppapp_path = full_path + '.ppapp' #ppapp = prefixes per as, per peer

        f = open(txtrib_path)
        normrib = open(normrib_path, 'w')

        # ppapp and ppp are keyed on peer_ip, or peer asn if there is no peer_ip
        ppapp = {}  # prefixes per as, per peer
        ppp = {}  # prefixes per peer
        peer_asns = {}
        null_peer_as_cache = {} # keyed on peer ip
        null_origin_as_cache = {} # keyed on prefix

        date_sort = extract_rib_date(txtrib_path).toordinal()
        date_str = extract_rib_date(txtrib_path).strftime('%Y-%m-%d')

        for line in f:
            try:
                components = line.split()
                [prefix, prefix_len] = components[0].split('/')
                peer_ip = components[1]
                raw_as_path = components[2:]
                if raw_as_path[0] == '-':  # null AS -- find observer and peer ASNs
                    if components[0] not in null_origin_as_cache:
                        output = subprocess.Popen(
                            "grep -P -m 1 '{0} (\d+\.)+\d+ \d+' {1}".format(
                            components[0], txtrib_path), shell=True,
                            stdout=subprocess.PIPE).communicate()[0]
                        null_origin_as_cache[components[0]] = output.split()[-1]
                    raw_as_path = [null_origin_as_cache[components[0]]]
                    if peer_ip not in null_peer_as_cache:
                        output = subprocess.Popen(
                            "grep -P -m 1 '{0} \d+' {1}".format(
                            peer_ip, txtrib_path), shell=True,
                            stdout=subprocess.PIPE).communicate()[0]
                        null_peer_as_cache[peer_ip] = output.split()[2]
                    raw_as_path.insert(0, null_peer_as_cache[peer_ip])
                    print("NULL AS_PATH: replacing '{0}' with {1}".format(
                        line.strip(), raw_as_path))
                # TODO capture notes/output from normalize_as_path
                norm_path = aspath.normalize_as_path(raw_as_path)
                if norm_path:
                    norm_path.reverse()
            except ValueError as e:
                norm_path = None

            if norm_path:
                if use_db:
                    origins_file.write("{0},{1},{2},{3},{4}\n".format(
                        '/'.join([prefix, prefix_len]),
                        get_peerid(norm_path[-1], peer_ip),
                        norm_path[0], date_sort, date_str))
                normrib.write("{0:<18} {1:<15} {2}\n".format(
                    '/'.join([prefix, prefix_len]), peer_ip,
                    aspath.path_to_string(norm_path)))
                try:
                    ppapp.setdefault(peer_ip, {})[norm_path[0]] += 1
                    ppp[peer_ip] += 1
                except KeyError:
                    ppapp.setdefault(peer_ip, {}).setdefault(norm_path[0], 1)
                    ppp.setdefault(peer_ip, 1)
                if peer_ip not in peer_asns:
                    peer_asns[peer_ip] = norm_path[-1]
            else:
                print("INVALID AS_PATH: dropping '{0}'".format(line.strip()))
        normrib.close()
        f.close()

        if use_db:
            for peer_ip in ppapp:
                for origin_as in ppapp[peer_ip]:
                    # TODO include notes
                    peerid = get_peerid(peer_asns[peer_ip], peer_ip)
                    peersum_file.write("{0},{1},{2},{3}\n".format(
                        date_str, origin_as, peerid, ppapp[peer_ip][origin_as]))
        ppapp_file = open(ppapp_path,'w')
        peers_file = open(peers_path,'w')
        #   ppapp_file.write("# prefix_count origin_as peer_as peer_ip\n")
        #   peers_file.write("# prefix_count peer_as peer_ip\n")
        for peer_ip in ppapp:
            for asn in ppapp[peer_ip]:
                ppapp_file.write('{0:>8} {1:>10} {2:>5} {3:<15}\n'.format(
                    ppapp[peer_ip][asn], asn, peer_asns[peer_ip], peer_ip))
        for peer_ip in ppp:
            peers_file.write('{0:>8} {1:>5} {2:<15}\n'.format(
                ppp[peer_ip], peer_asns[peer_ip], peer_ip))
        ppapp_file.close()
        peers_file.close()

    if use_db:
        peersum_file.close()
        origins_file.close()


def process_txtrib_mp(txtrib_files, num_processes, output_dir, use_db):
    txtrib_files.sort(key=extract_rib_date)
    worker_files = [None]*num_processes
    files_per = int(math.ceil(len(txtrib_files)/float(num_processes)))
    for wi in xrange(num_processes):
        worker_files[wi] = [os.path.abspath(path) for path in
            txtrib_files[wi*files_per:(wi+1)*files_per]]
    peer_map = None
    output_dir = None
    if use_db:
        manager = Manager()
        peer_map = manager.dict()
        output_dir = "/home/woodrow/proj/cidr-report_analysis/mptest"
    workers = [
        Process(target=process_txtrib_worker,
        args=(worker_files[i], output_dir, peer_map, use_db))
        for i in xrange(num_processes)]
    for process in workers:
        process.start()
    for process in workers:
        process.join()
    if peer_map:
        f = open(os.path.join(output_dir,'peers.csv'), 'w')
        f.write("# generated on {0} UTC\n".format(datetime.datetime.utcnow()))
        f.write("# peer_id,peer_as,peer_ip\n")
        for peer in peer_map.keys():
            peer_id = peer_map[peer]
            f.write("{0},{1[0]},{1[1]}\n".format(peer_id, peer))
        f.close()
    if use_db:
        # stitch
        pass


if __name__ == '__main__':
    main()
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
