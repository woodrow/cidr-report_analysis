import cidr_report
import psycopg2
import collections
import datetime
import sys
import os

# CRDelta objects are defined as the difference between the official CIDR
# Report and the generated CIDR Report. In other words:
#   CRDelta.delta_netgain = OfficialCR.netgain - GeneratedCR.netgain
# and the same ordering applies for similar delta_* quantities
CRDelta = collections.namedtuple('CRDelta',
    ('date origin_as ecr_rank gcr_rank ecr_netgain gcr_netgain '
     'ecr_netsnow gcr_netsnow'))


def compare_report(gen_report_file, conn):
    gcr_dict = {}
    for line in gen_report_file:
        if line[0] != '#':
            components = line.split(',')
            cr_row = cidr_report.CRRow(
                asnum=int(components[1]),
                rank=int(components[2]),
                netsnow=int(components[4]),
                netsaggr=int(components[7]),
                netgain=int(components[8]),
                netname=None)
            gcr_dict[cr_row.asnum] = cr_row
    date = datetime.datetime.strptime(components[0], '%Y-%m-%d').date()
    ecr = cidr_report.get_from_db(date, conn)
    delta_list = []
    for row in ecr.rank_list:
        try:
            delta_list.append(CRDelta(
                date=date,
                origin_as=row.asnum,
                ecr_rank = row.rank,
                ecr_netgain = row.netgain,
                ecr_netsnow = row.netsnow,
                gcr_rank = gcr_dict[row.asnum].rank,
                gcr_netgain = gcr_dict[row.asnum].netgain,
                gcr_netsnow = gcr_dict[row.asnum].netsnow))
        except KeyError:
            delta_list.append(CRDelta(
                date=date,
                origin_as=row.asnum,
                ecr_rank = row.rank,
                ecr_netgain = row.netgain,
                ecr_netsnow = row.netsnow,
                gcr_rank = None,
                gcr_netgain = None,
                gcr_netsnow = None))
    return delta_list


def compare_reports(gen_report_paths):
    conn = psycopg2.connect(database='woodrow',
        user='woodrow', password='woodrow$mitas-2@2011',
        host='mitas-2.csail.mit.edu')
    compare_deltas = []
    for report_path in gen_report_paths:
        report_file = open(report_path)
        compare_deltas.append(compare_report(report_file, conn))
        report_file.close()
    conn.close()
    return compare_deltas


if __name__ == '__main__':
    if len(sys.argv) == 2:
        crdelta_list = compare_reports([os.path.abspath(sys.argv[1])])[0]
        print("Deltas for {0}".format(crdelta_list[0].date))
        print(
"   origin |       rank      |       netgain       |       netsnow      ")
        print(
"       as | ecr | gcr | del |  ecr |  gcr |   del |  ecr |  gcr |   del")
        print(
"----------+-----+-----+-----+------+------+-------+------+------+------")
        for delta in crdelta_list:
            print(("{0.origin_as:>9} | "
                   "{0.ecr_rank:>3} | "
                   "{0.gcr_rank:>3} | "
                   "{1:>3} | "
                   "{0.ecr_netgain:>4} | "
                   "{0.gcr_netgain:>4} | "
                   "{2:>5} | "
                   "{0.ecr_netsnow:>4} | "
                   "{0.gcr_netsnow:>4} | "
                   "{3:>5}").format(delta,
                   delta.ecr_rank - delta.gcr_rank,
                   delta.ecr_netgain - delta.gcr_netgain,
                   delta.ecr_netsnow - delta.gcr_netsnow))
    else:
        print("USAGE: {0} PATH_TO_CIDRREPORT".format(sys.argv[0]))
