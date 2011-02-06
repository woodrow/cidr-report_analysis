import sys
import datetime
import os.path
import re
import collections
import pydoc

EPOCH = datetime.date(1996, 9, 13) #datetime.date(2000, 12, 22)
CRRow = collections.namedtuple('CRRow', 'asnum netsnow netsaggr netgain')
CRWeek = collections.namedtuple('CRWeek', 'date week file rank_list')

def main(file_paths=[]):
    num_weeks = ((datetime.date(2011, 01, 31) - EPOCH).days // 7) + 1
    data = [None]*num_weeks
    dup_count = 0
    for fp in file_paths:
        f = open(fp)
        text = ''.join(f.readlines())
        table = re.search('--- (\d{2}\S{3}\d{2}) ---.*?\n(.*?)(?:\n\n\n|\n\n[^\n]*--- (\d{2}\S{3}\d{2}) ---)',
            text, re.I|re.M|re.S)
        aggr_table = table.groups()[1].split('\n')
        date = datetime.datetime.strptime(table.groups()[0], '%d%b%y').date()
        week = (date - EPOCH).days // 7
        rank = 0
        rank_list = [None]*30
        for line in aggr_table:
            components = line.split()
            if len(components) > 0 and re.match('AS\d+', components[0]):
                assert rank < 30
                rank_list[rank] = CRRow(asnum=int(components[0][2:]),
                    netsnow=int(components[1]), netsaggr=int(components[2]),
                    netgain=int(components[3]))
                rank += 1
        if rank < 30: # why isn't the rank 30? take a closer look
            print(fp)
            print("UNEXPECTED RANK: {0}".format(rank))
        if not data[week]:
            data[week] = CRWeek(date, week, fp, rank_list)
        else:
            dup_count += 1
            print("DUPLICATE DATA for week {0}".format(week))
            print("    existing:\n    date: {0}\n    file: {1}".format(
                data[week]['date'], data[week]['file']))
            print("    new:\n    date: {0}\n    file: {1}".format(date, fp))
    if dup_count:
        print("-----\nTOTAL DUPES: {0}\n-----".format(dup_count))
    return data


if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_paths = sys.argv[1:]
        data = main(file_paths)
        none_count = sum((1 for x in data if x is None))
        non_none_count = sum((1 for x in data if x is not None))
        total = len(data)
        print("{0} missing weeks, {1} weeks with data, {2} weeks total".format(
            none_count, non_none_count, total))
        df = open('dotfile_out.dot', 'w')
        df.write('strict graph {\n')
        last_week = None
        for i in xrange(min(len(data), 200)):
            if data[i]:
                df.write('week{0}row0 [label="Week {0}\\n{1}", shape=box, style=filled, fillcolor=white];\n'.format(i, data[i].date))
                for r in xrange(min(len(data[i].rank_list),5)):
                    df.write('week{0}row{1} [label="AS {2.asnum}\\n{2.netgain}/{2.netsnow}", shape=ellipse, style=filled, fillcolor=white];\n'.format(i, r+1, data[i].rank_list[r]))
                    df.write('week{0}row{1} -- week{0}row{2} [style=solid];\n'.format(i, r, r+1))
                # compare and make connections with 'last week'
                last_week = i
            else:
                df.write('week{0}row0 [label="Week {0}", shape=box, style=filled, fillcolor=tomato];\n'.format(i))
        df.write('}\n')
        df.close()

    else:
        print("USAGE: ...")

#strict graph {
## structure
#    a -- b [style=invis];
#        b -- c [style=invis];
#        c -- d [style=invis];
#
#        w -- x [style=invis];
#        x -- y [style=invis];
#        y -- z [style=invis];
#
## rank changes
#        a -- y [constraint=false];
#        b -- w [constraint=false];
#        c -- x [constraint=false];
#        d -- z [constraint=false];
#}
