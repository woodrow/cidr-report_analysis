#!/usr/bin/python2.6

import pickle
import pydoc
import sys
import re
import os
import urllib2
import hashlib

SUBDIR = 'triage_output'


def process_files(files, resume_index, resume_line):
    new_archive_cache = {}
    try:
        for fi in xrange(max(0, resume_index), len(files)):
            f = open(files[fi])
            li = 0  # line 1 is the first line
            for line in f:
                li += 1
                if li < max(1, resume_line):
                    continue
                file_str = "# from {0}:{1}\n".format(files[fi], li)
                [date, subject, sender, loc] = line.split('\t')
                file_str += "# {0} '{1}' from '{2}'\n# {3}\n".format(
                    date, subject, sender, loc)
                if line.find('http') > -1:  # old-style archives
                    url = loc
                    try:
                        response = get_url(url)
                    except urllib2.HTTPError, e:
                        print("ERROR " + url + ": " + str(e))
                        if(e.code in [400, 401, 403, 500, 503]):
                            break
                        else:
                            continue
                    url_content = ''.join(response.readlines())
                    [header, body] = re.search((
                        '<!--X-Subject-Header-Begin-->(.*?)'
                        '<!--X-Subject-Header-End-->.*?'
                        '<!--X-Body-of-Message-->(.*?)'
                        '<!--X-Body-of-Message-End-->'),
                        url_content, re.DOTALL).groups()
                    header = re.sub('<.*?>','', header)
                    header = re.sub('\n+', '\n', header)
                    header.strip()
                    body = re.sub('<.*?>','', body)
                    file_str += '\n'.join([header, body])

                else:  # new-style archives
                    [filename,line_range] = loc.split(':')
                    [line_start, line_end] = [
                        int(x) for x in line_range.split('-')]
                    filename = os.path.abspath(
                        os.path.join(os.path.dirname(files[fi]), filename))
                    if filename not in new_archive_cache:
                        f = open(filename)
                        new_archive_cache[filename] = f.readlines()
                        f.close()
                    file_str += ''.join(
                        new_archive_cache[filename][line_start:line_end])

                # show file_str
                pydoc.pager(file_str)
                # take my input [yes, no, interesting, view again]
                while True:
                    user_input = raw_input(str(
                        colorkey('y') + "es, " +
                        colorkey('n')+"o, " +
                        colorkey('i') + "nteresting, " +
                        colorkey('v') +"iew again" + ": ")).strip() #, or [quit]
                    if len(user_input) > 0:
                        if user_input[0] in ['y', 'n', 'i']:
                            if user_input[0] == 'y':
                                f = open(os.path.join(
                                    SUBDIR, 'cidr_' + date[:10] + '_' +
                                    hashlib.sha1(file_str).hexdigest() +
                                    '.txt'), 'w')
                                f.write(file_str)
                                f.close()
                            elif user_input[0] == 'i':
                                f = open(os.path.join(
                                    SUBDIR, 'int_' + date[:10] + '_' +
                                    hashlib.sha1(file_str).hexdigest() +
                                    '.txt'), 'w')
                                f.write(file_str)
                                f.close()
                            break
                        elif user_input[0] == 'v':
                            pydoc.pager(file_str)

        # done -- clear data to be pickled, as there's no state left to save
        files = []
        fi = -1
        li = -1
        raise KeyboardInterrupt
    except (KeyboardInterrupt, EOFError):
        pickle_file = open('triage_state.pickle', 'w')
        resume_dict = {}
        resume_dict['files'] = files
        resume_dict['resume_index'] = fi
        resume_dict['resume_line'] = li
        pickle.dump(resume_dict, pickle_file)
        pickle_file.close()
        raise


def get_url(url):
    req = urllib2.Request(url, data=None, headers={
        'User-agent':
        "Mozilla/5.0 (compatible; ptolemy/0.1; +http://ptolemy.csail.mit.edu)"})
    response = urllib2.urlopen(req)
    if response == None:
        raise urllib2.URLError("timeout")
    if response.geturl() != req.get_full_url():
        raise urllib2.URLError(
            "URL mismatch: requested '" + req.get_full_url() +
            "'; received '" + response.geturl() + "'")
    return response


def colorkey(key):
    return "[\033[32m" + key + "\033[0m]"


def main():
    files = []
    resume_dict = {}
    resume_index = -1
    resume_line = -1
    if len(sys.argv) > 1:
        files = [os.path.abspath(p) for p in sys.argv[1:]]
    else:  # try to restore
        try:
            rf = open('triage_state.pickle')
            resume_dict = pickle.load(rf)
            rf.close()
            files = resume_dict['files']
            resume_index = resume_dict['resume_index']
            resume_line = resume_dict['resume_line']
        except (IOError, AttributeError):
            print("State restore error")

    if files:
        process_files(files, resume_index, resume_line)
    else:
        print("  USAGE: {0} FILE ...".format(sys.argv[0]))


if __name__ == '__main__':
    main()