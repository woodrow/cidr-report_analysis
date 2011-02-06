import sys
import datetime
import os.path
import re
import collections
import pydoc

EPOCH = datetime.date(1996, 9, 13) #datetime.date(2000, 12, 22)
CRRow = collections.namedtuple('CRRow', 'asnum netsnow netsaggr netgain')
CRWeek = collections.namedtuple('CRWeek', 'date week file rank_list')

MAX_WEEKS_PLOT = 751 # 800
MAX_ROWS_PLOT = 30 # 30
ROW_SPACE = 98
COL_SPACE = 150

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
        none_list = [i for i in xrange(len(data)) if data[i] is None]
        non_none_count = sum((1 for x in data if x is not None))
        total = len(data)
        print("--- missing weeks ---")
        for weeknum in none_list:
            print("  {0:>3}: {1}".format(
                weeknum, EPOCH + datetime.timedelta(weeks=weeknum)))
        print("----------")
        print("Summary Information:")
        print("{0} missing weeks, {1} weeks with data, {2} weeks total".format(
            len(none_list), non_none_count, total))
        freq_dict = collections.defaultdict(lambda: 0)
        weighted_freq_dict = collections.defaultdict(lambda: 0)
        for week in data:
            if week:
                weight = 30
                for row in week.rank_list:
                    freq_dict[row.asnum] += 1
                    weighted_freq_dict[row.asnum] += weight
                    weight -= 1

        print("Total ASes seen on the CIDR report: {0}".format(len(freq_dict)))
        freq_list = [x for x in freq_dict.iteritems()]
        wfreq_list = [x for x in weighted_freq_dict.iteritems()]
        freq_list.sort(key=lambda x: x[1], reverse=True)
        wfreq_list.sort(key=lambda x: x[1], reverse=True)
        print("---")
        print("Top 10 most frequent appearances:")
        for i in xrange(10):
            print("AS{0[0]:<6}: {0[1]} weeks".format(freq_list[i]))
        for i in xrange(10):
            print("AS{0[0]:<6}: {0[1]} rank-weeks".format(wfreq_list[i]))

        contrast_color_list = ['yellow1',
            'purple',
            'orange',
            'dodgerblue4',
            'red2',
            'springgreen3',
            'goldenrod1',
            'mediumpurple4',
            'chocolate2',
            'turquoise3',
            'deeppink3',
            'chartreuse3']

        color_map = {}
        for i in xrange(len(wfreq_list)):
            color_map[wfreq_list[i][0]] = contrast_color_list[i%12]

        # TODO print number ASes on the chart
        # TODO determine AS frequency on chart (# of weeks)
        # TODO figure out a way of coloring them uniquely -- sort by freq, then
        # pick contrasting colors?

        df = open('dotfile_out.dot', 'w')
        df.write('strict graph {\ngraph[ordering=out, outputorder=nodesfirst, splines=false];\n')
        #df.write('root [style=invis];\n')
        last_week = -1
#        for i in xrange(min(len(data), MAX_WEEKS_PLOT)):
#            if data[i]:
#                df.write('week{0}row0 [label="Week {0}\\n{1}", shape=box, style=filled, fillcolor=white];\n'.format(i, data[i].date))
#            else:
#                df.write('week{0}row0 [label="Week {0}\\nYYYY-MM-DD", shape=box, style=filled, fillcolor=tomato];\n'.format(i))

        for i in xrange(min(len(data), MAX_WEEKS_PLOT)):
            rows = min(len(data), MAX_WEEKS_PLOT)
            if data[i]:
                df.write('week{0}row0 [label="Week {0}\\n{1}", shape=box, style=filled, fillcolor=white, pos="{2},{3}", pin=true];\n'.format(i, data[i].date, i*COL_SPACE+59, rows*ROW_SPACE+22))
                for r in xrange(min(len(data[i].rank_list), MAX_ROWS_PLOT)):
                    df.write('week{0}row{1} [label="AS {2.asnum}\\n{2.netgain}/{2.netsnow}", shape=ellipse, style=filled, fillcolor=white, pos="{3},{4}", pin=true, color={5}, penwidth=12];\n'.format(i, r+1, data[i].rank_list[r], i*COL_SPACE+59, (rows-r-1)*ROW_SPACE+22, color_map[data[i].rank_list[r].asnum]))
                    df.write('week{0}row{1} -- week{0}row{2} [style=invis];\n'.format(i, r, r+1))
                    if last_week >= 0:
                        for j in xrange(min(len(data[last_week].rank_list),
                            MAX_ROWS_PLOT)):
                            if data[i].rank_list[r].asnum == data[last_week].rank_list[j].asnum:
                                df.write('week{0}row{1} -- week{2}row{3} [constraint=false, penwidth=12, color={4}];'.format(i, r+1, last_week, j+1, color_map[data[i].rank_list[r].asnum]))
                last_week = i
            else:
                df.write('week{0}row0 [label="Week {0}", shape=box, style=filled, fillcolor=tomato, pos="{1},{2}", pin=true];\n'.format(i, i*COL_SPACE+59, rows*ROW_SPACE+22))
#                for r in xrange(min(30, MAX_ROWS_PLOT)):
#                    df.write('week{0}row{1} [label="AS ???\\n???/???", shape=ellipse, style=filled, fillcolor=tomato pos="{2},{3}, pin=true"];\n'.format(i, r+1, i*123+59, (rows-r-1)*98+22))
#                    df.write('week{0}row{1} -- week{0}row{2} [style=invis];\n'.format(i, r, r+1))
#                    if i > 0:
#                        df.write('week{0}row{2} -- week{1}row{2} [style=solid, contraint=false];\n'.format(i-1, i, r+1))
#                        try:
#                            if data[i+1]:
#                                df.write('week{0}row{2} -- week{1}row{2} [style=solid, contraint=false];\n'.format(i, i+1, r+1))
#                        except IndexError:
#                            pass

#            if i > 0:
#                df.write('week{0}row0 -- week{1}row0 [constraint=false];'.format(i-1, i))
            #df.write('root -- week{0}row0 [style=invis];'.format(i))
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
