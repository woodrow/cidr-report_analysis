#!/usr/bin/env python2.6

import os
import gzip
import subprocess
import re
import shutil

BGPDUMP_PATH = os.path.realpath(
    '../../libbgpdump/libbgpdump-1.4.99.13/simpledump')
STRAIGHTENRV_PATH = os.path.realpath(
    '../../rv2atoms/rv2atoms-0.5/bin/straightenRV')

def process_rib(full_path, include_peer_ip=True):
    print(STRAIGHTENRV_PATH)
    dir_name = os.path.dirname(full_path)
    base_name = '.'.join(os.path.basename(full_path).split('.')[:-1])
    # full_name contains the full path to the RIB file without an extension
    full_name = os.path.join(dir_name, base_name)

    # filenames
    log_name = full_name + '.process_rib_log'
    txt_name = full_name + '.txt'

    # generate routing table txt file
    print("Generating .txt routing table.")
    if full_name.find('oix-full') == -1:
        # new (MRT) table
        # TODO capture debugging output
        output = subprocess.Popen(' '.join([BGPDUMP_PATH,
            '-p' if include_peer_ip else '', full_path, txt_name]),
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
            cwd=dir_name, shell=True).communicate()[0]
        print(output)
    else:
        # old (Cisco console dump) table
        # TODO do something with remainder of output?
        output = subprocess.Popen(
            ' '.join([STRAIGHTENRV_PATH, '-m all -d 1', full_path]),
            stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
            cwd=dir_name, shell=True).communicate()[0]
        print(output)
        out_name = re.search('Output filenames start with: (.*?)\n',
            output).groups()[0]
        infile = gzip.open(os.path.join(dir_name, out_name + '.full.gz'))
        outfile = open(txt_name, 'w')
        for line in infile:
            try:  # ignore comments
                line = line[0:line.find('#')]
            except ValueError:
                pass
            components = line.strip().split()
            try:
                outfile.write('{0} {1} {2}\n'.format(
                    components[2], components[3], ' '.join(components[5:-1])))
            except IndexError:
                pass
        outfile.close()
        infile.close()
        subprocess.check_call('rm ' + os.path.join(dir_name, out_name) + '*',
            shell=True)
