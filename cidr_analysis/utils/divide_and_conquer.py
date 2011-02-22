#!/usr/bin/python2.7

import multiprocessing
import os
import sys
import subprocess


def main():
    for path in sys.argv[1:]:
        subprocess.check_call('split -l 25000000 {0} {0}_chunk'.format(path), shell=True)

    input_queue = multiprocessing.Queue()
    output_queue = multiprocessing.Queue()

    chunk_list = subprocess.check_output('ls ' + ' '.join(('{0}_chunk*'.format(x) for x in sys.argv[1:])), shell=True)
    chunk_path_list = [os.path.abspath(x) for x in chunk_list.split()]
    for chunk_path in chunk_path_list:
        sort_queue.put(chunk_path)



# create pool of sorters
# let pool loose on queue, returning output queue
# let new workers loose on output queue
#  # new workers pull 2 from queue, merge, put merged filename into output queue, and delete input files
#  # repeat until there's one file left
