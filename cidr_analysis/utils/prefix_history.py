#!/usr/bin/python2.6

#from multiprocessing import Pool, Process, Queue
import sys
import os.path
import collections
import datetime
import subprocess

POweek = collections.namedtuple('POweek', 'peerid origin_as ord_date')


class PORecord(object):
    def __init__(self, prefix, peerid, origin_as, date_effective,
        weeks_visible=''):
        self.prefix = prefix
        self.peerid = peerid
        self.origin_as = origin_as
        self.date_effective = date_effective
        self.last_seen = date_effective
        self.weeks_visible = weeks_visible


#def process_prefix(prefix, prefix_lines, end_date, path):
def process_prefix(prefix, prefix_lines, end_date, row_serial):
    prefix_lines.sort(key=lambda x: x.peerid * 1e6 + x.ord_date)
    current_porecord = PORecord(
        prefix, prefix_lines[0].peerid, prefix_lines[0].origin_as,
        datetime.date.fromordinal(prefix_lines[0].ord_date), weeks_visible='1')
    complete_porecord = None

    for p in prefix_lines[1:]:
        if p.peerid != current_porecord.peerid:
            # fill current POrecord.weeks_visible with 0s until end_date
            current_porecord.weeks_visible += '0' * (
                ((end_date - current_porecord.date_effective).days // 7 + 1) -
                len(current_porecord.weeks_visible))
            complete_porecord = current_porecord
        elif p.origin_as != current_porecord.origin_as:
            # fill current POrecord.weeks_visible with 0s until p.ord_date
            current_porecord.weeks_visible += '0' * (
                ((datetime.date.fromordinal(p.ord_date) -
                current_porecord.date_effective).days // 7 + 1) -
                len(current_porecord.weeks_visible))
            complete_porecord = current_porecord

        if complete_porecord:
            print((
                "{1[0]},{0.prefix},{0.peerid},{0.origin_as},"
                "{0.date_effective},{0.last_seen},{0.weeks_visible},{2}"
                ).format(complete_porecord, row_serial,
                sum((1 for x in complete_porecord.weeks_visible if x == '1'))))
            row_serial[0] += 1
#            weeks_visible = sum((1 for x in complete_porecord.weeks_visible if x == '1'))
#            weeks_grepped = int(subprocess.Popen(
#                "grep '{0.prefix},{0.peerid},{0.origin_as}' {1} | wc -l".format(
#                complete_porecord, path), shell=True,
#                stdout=subprocess.PIPE).communicate()[0].strip())
#            if weeks_visible != weeks_grepped:
#                print("ERROR in above prefix!!!")
            current_porecord = PORecord(
                prefix, p.peerid, p.origin_as,
                datetime.date.fromordinal(p.ord_date))
            complete_porecord = None

        weeks_since_last_record = (
            (p.ord_date - current_porecord.date_effective.toordinal()) // 7 -
            len(current_porecord.weeks_visible))
        if weeks_since_last_record + 1 >= 0:
            current_porecord.weeks_visible += '0' * weeks_since_last_record
            current_porecord.weeks_visible += '1'
        current_porecord.last_seen = datetime.date.fromordinal(p.ord_date)

    # handle last partially incomplete object
    current_porecord.weeks_visible += '0' * (
        ((end_date - current_porecord.date_effective).days // 7 + 1) -
        len(current_porecord.weeks_visible))
    print((
        "{1[0]},{0.prefix},{0.peerid},{0.origin_as},{0.date_effective},"
        "{0.last_seen},{0.weeks_visible},{2}"
        ).format(current_porecord, row_serial,
        sum((1 for x in current_porecord.weeks_visible if x == '1'))))
    row_serial[0] += 1
#    weeks_visible = sum((1 for x in current_porecord.weeks_visible if x == '1'))
#    weeks_grepped = int(subprocess.Popen(
#        "grep '{0.prefix},{0.peerid},{0.origin_as}' {1} | wc -l".format(
#        current_porecord, path), shell=True,
#        stdout=subprocess.PIPE).communicate()[0].strip())
#    if weeks_visible != weeks_grepped:
#        print("ERROR in above prefix!!!")


def gen_prefix_origin_records(path, end_date):
    f = open(path)
    current_prefix = None
    current_prefix_lines = []
    row_serial = [1]
    for line in f:
        components = line.strip().split(',')
        if len(components) == 4:
            if components[0] != current_prefix:
                if current_prefix_lines:
                    # record = process_prefix
                    process_prefix(
                        current_prefix, current_prefix_lines, end_date,
                        row_serial)
                current_prefix = components[0]
                current_prefix_lines = []

            current_prefix_lines.append(
                POweek(peerid=int(components[1]),
                origin_as=int(components[2]),
                ord_date=int(components[3])))

    # handle last partially incomplete object
    process_prefix(current_prefix, current_prefix_lines, end_date, row_serial)


def usage():
    print("USAGE " + sys.argv[0] + " end_date FILE")
    print("""  end date (YYYY-MM-DD format)""")


def main():
    if len(sys.argv) == 3:
        end_date = datetime.datetime.strptime(sys.argv[1], '%Y-%m-%d').date()
        path = os.path.abspath(sys.argv[2])
        gen_prefix_origin_records(path, end_date)
    else:
        usage()


if __name__ == '__main__':
    main()
