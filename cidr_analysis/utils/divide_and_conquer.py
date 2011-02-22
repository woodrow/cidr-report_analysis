#!/usr/bin/python2.7

from multiprocessing import Queue, Pool
import os
import sys
import subprocess
import hashlib
import time

def chunk_sort_worker(in_queue, out_queue):
    try:
        path = in_queue.get_nowait()
        out_path = path + '-sorted'
        subprocess.check_call("sort -T /home/cidr_analysis/tmp/ " +
            "-t ',' -s -k 1,1 -o {1} {0}".format(path, out_path), shell=True)
        out_queue.put_nowait(out_path)
    except Queue.Empty:
        return


def chunk_merge_worker(in_queue, out_queue):
    try:
        path_1 = path_2 = None
        path_1 = in_queue.get_nowait()
        path_2 = in_queue.get_nowait()
        out_hash = hashlib.sha1(path_1 + path_2).hexdigest()
        out_path = os.path.join(os.path.dirname(path_1), out_hash)
        subprocess.check_call("sort -m -T /home/cidr_analysis/tmp/ " +
            "-t ',' -s -k 1,1 -o {2} {0} {1}".format(path_1, path_2, out_path),
            shell=True)
        subprocess.check_call('rm {0} {1}'.format(path_1, path_2), shell=True)
        out_queue.put_nowait(out_path)
    except Queue.Empty:
        if path_1:
            out_queue.put_nowait(path_1)
        return


def print_deltat(msg, t1, t2):
    print '%s took %0.3f s' % (msg, t2-t1)


def main():
    input_paths = [os.path.abspath(x) for x in sys.argv[1:]]
    print("Splitting input files...")
    t1 = time.time()
    for path in input_paths:
        subprocess.check_call('split -l 25000000 {0} {0}-chunk_'.format(path),
            shell=True)
    t2 = time.time()
    print_deltat("Splitting input files", t1, t2)

    sort_queue = Queue()
    done_queue = Queue()

    chunk_list = subprocess.check_output('ls ' +
        ' '.join(('{0}_chunk*'.format(x) for x in input_paths)), shell=True)
    chunk_path_list = [os.path.abspath(x) for x in chunk_list.split()]
    for chunk_path in chunk_path_list:
        sort_queue.put_nowait(chunk_path)

    print("Sorting chunks...")
    t1 = time.time()
    pool = Pool(processes=10)
    pool.apply_async(chunk_sort_worker, (sort_queue, done_queue))
    pool.close()
    pool.join()
    t2 = time.time()
    print_deltat("Sorting chunks", t1, t2)

    merge_queue = Queue()
    while done_queue.qsize() > 1:
        print_str = "Merging {0} chunks".format(done_queue.qsize())
        print(print_str)
        (merge_queue, done_queue) = (done_queue, merge_queue)
        t1 = time.time()
        pool = Pool(processes=10)
        pool.apply_async(chunk_merge_worker, (merge_queue, done_queue))
        pool.close()
        pool.join()
        t2 = time.time()
        print_deltat(print_str, t1, t2)

    merged_path = done_queue.get_nowait()
    output_path = os.path.join(os.path.dirname(merged_path),
        'prefix_origins-merged.csv')
    subprocess.check_call('mv {0} {1}'.format(merged_path, output_path))

# create pool of sorters
# let pool loose on queue, returning output queue
# let new workers loose on output queue
#     new workers pull 2 from queue, merge, put merged filename into output
#     queue, and delete input files; repeat until there's one file left
