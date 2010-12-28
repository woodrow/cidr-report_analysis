#!/usr/bin/env python2.6

import os
import sys
import re

BGPDUMP_PATH = os.path.realpath(
    '../libbgpdump/libbgpdump-1.4.99.13/simpledump')
STRAIGHTENRV_PATH = os.path.realpath(
    '../rv2atoms-0.5/bin/straightenRV')

def process_rib(full_path, include_peer_ip=False):
    dir_name = os.path.dirname(full_path)
    base_name = '.'.join(os.path.basename(full_path).split('.')[:-1])
    full_name = os.path.join(dir_name, base_name)

    # filenames
    log_name = full_name + '.neighbors_log'
    txt_name = full_name + '.txt'

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



