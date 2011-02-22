#!/usr/bin/python2.6

#from multiprocessing import Pool, Process, Queue
import sys
import os.path
import collections
import datetime

POweek = collections.namedtuple('POweek', 'peerid origin_as ord_date')


class PORecord(object):
    def __init__(self, prefix, peerid, origin_as, date_effective,
        weeks_seen=''):
        self.prefix = prefix
        self.peerid = peerid
        self.origin_as = origin_as
        self.date_effective = date_effective
        self.weeks_seen = weeks_seen


def process_prefix(prefix, prefix_lines, end_date):
    prefix_lines.sort(key=lambda x: x.peerid * 1e6 + x.ord_date)
    current_porecord = PORecord(
        prefix, prefix_lines[0].peerid, prefix_lines[0].origin_as,
        datetime.date.fromordinal(prefix_lines[0].ord_date))
    complete_porecord = None

    for p in prefix_lines[1:]:
        if p.peerid != current_porecord.peerid:
            # fill current POrecord.weeks_seen with 0s until end_date
            current_porecord.weeks_seen += '0' * (
                ((end_date - current_porecord.date_effective).days // 7 + 1) -
                len(current_porecord.weeks_seen))
            complete_porecord = current_porecord
        elif p.origin_as != current_porecord.origin_as:
            # fill current POrecord.weeks_seen with 0s until p.ord_date
            current_porecord.weeks_seen += '0' * (
                ((datetime.date.fromordinal(p.ord_date) -
                current_porecord.date_effective).days // 7 + 1) -
                len(current_porecord.weeks_seen))
            complete_porecord = current_porecord

        if complete_porecord:
            print(
                ("{0.prefix},{0.peerid},{0.origin_as},{0.date_effective},"
                "B'{0.weeks_seen}'").format(complete_porecord))
            current_porecord = PORecord(
                prefix, p.peerid, p.origin_as,
                datetime.date.fromordinal(p.ord_date))
            complete_porecord = None

        # replace with bitstring?
        current_porecord.weeks_seen += '0' * (
            ((datetime.date.fromordinal(p.ord_date) -
            current_porecord.date_effective).days // 7) -
            len(current_porecord.weeks_seen))
        current_porecord.weeks_seen += '1'

    # handle last partially incomplete object
    current_porecord.weeks_seen += '0' * (
        ((end_date - current_porecord.date_effective).days // 7 + 1) -
        len(current_porecord.weeks_seen))
    print(
        ("{0.prefix},{0.peerid},{0.origin_as},{0.date_effective},"
        "B'{0.weeks_seen}'").format(current_porecord))


def gen_prefix_origin_records(path, end_date):
    f = open(path, 'r')
    current_prefix = None
    current_prefix_lines = []
    for line in f:
        components = line.strip().split(',')
        if len(components) == 5:
            if components[0] != current_prefix:
                # record = process_prefix
                process_prefix(current_prefix, current_prefix_lines, end_date)
                current_prefix = components[0]
                current_prefix_lines = []

            current_prefix_lines.append(
                POweek(peerid=int(components[1]),
                origin_as=int(components[2]),
                ord_date=int(components[3])))

    # handle last partially incomplete object
    process_prefix(current_prefix, current_prefix_lines, end_date)


def main():
    end_date = None
    path = os.path.abspath(sys.argv[1])
    if len(sys.argv) == 4:
        end_date = datetime.datetime.strptime(sys.argv[3], '%Y-%m-%d').date()
    gen_prefix_origin_records(path, end_date)


if __name__ == '__main__':
    main()
