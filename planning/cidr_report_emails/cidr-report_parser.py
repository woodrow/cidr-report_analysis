#!/usr/bin/python2.6

import sys
import datetime
import os.path
import re
import collections
import pydoc

EPOCH = datetime.date(1996, 9, 13) #datetime.date(2000, 12, 22)
CRRow = collections.namedtuple('CRRow', 'asnum netsnow netsaggr netgain rank')
CRWeek = collections.namedtuple('CRWeek', 'date week file rank_list')

MAX_WEEKS_PLOT = 751 # 800
MAX_ROWS_PLOT = 30 # 30
ROW_SPACE = 98
COL_SPACE = 150

def main(file_paths=[]):
    num_weeks = ((datetime.date(2011, 01, 31) - EPOCH).days // 7) + 1
    data = [None]*num_weeks
    peras_data = collections.defaultdict(lambda: [None]*num_weeks)
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
                    netgain=int(components[3]), rank=30-rank)
                peras_data[rank_list[rank].asnum][week] = rank_list[rank]
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
                data[week].date, data[week].file))
            print("    new:\n    date: {0}\n    file: {1}".format(date, fp))
    if dup_count:
        print("-----\nTOTAL DUPES: {0}\n-----".format(dup_count))
    return (data, peras_data)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_paths = sys.argv[1:]
        (data, peras_data) = main(file_paths)
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
        as_dict = collections.defaultdict(lambda: [])
        wfreq_dict = collections.defaultdict(lambda: 0)
        rwfreq_dict = collections.defaultdict(lambda: 0)
        for week in data:
            if week:
                weight = 30
                for row in week.rank_list:
                    as_dict[row.asnum].append(row)
                    wfreq_dict[row.asnum] += weight
                    rwfreq_dict[row.asnum] += row.netgain
                    weight -= 1

        print("Total ASes seen on the CIDR report: {0}".format(len(as_dict)))
        freq_list = [(x, len(as_dict[x])) for x in as_dict]
        wfreq_list = [x for x in wfreq_dict.iteritems()]
        rwfreq_list = [x for x in rwfreq_dict.iteritems()]
        freq_list.sort(key=lambda x: x[1], reverse=True)
        wfreq_list.sort(key=lambda x: x[1], reverse=True)
        rwfreq_list.sort(key=lambda x: x[1], reverse=True)
        print("---")
        print("Top 10 most frequent appearances...")
        print("by weeks on the list:")
        for i in xrange(min(10,len(freq_list))):
            print("  AS{0[0]:<6}: {0[1]} weeks".format(freq_list[i]))
        print("by rank-weeks on the list:")
        for i in xrange(min(10,len(wfreq_list))):
            print("  AS{0[0]:<6}: {0[1]} rank-weeks".format(wfreq_list[i]))
        print("by route-weeks (netgain-weeks) on the list:")
        for i in xrange(min(10,len(rwfreq_list))):
            print("  AS{0[0]:<6}: {0[1]} route-weeks".format(rwfreq_list[i]))

        print("Dumping frequency and weighted-frequency data: cr_freq.csv")
        f = open('cr_freq.csv', 'w')
        f.write("# asn,wfreq,rwfreq,freq\n")
        for e in wfreq_list:
            f.write("{0[0]},{0[1]},{2},{1}\n".format(
                e, len(as_dict[e[0]]), rwfreq_dict[e[0]]))
        f.close()


        import pickle
        f = open('peer_counts.pickle')
        table_totals = [None]*len(data)
        count_list = pickle.load(f)
        for item in count_list:
            date = datetime.datetime.strptime(item[0], '%Y-%m-%d').date()
            week = (date - EPOCH).days // 7
            table_totals[week] = item[2] # 1 is median, 2 is max
        i = 0
        start_interp = -1
        end_interp = -1
        while i <= len(table_totals):
            if i == len(table_totals) or table_totals[i]:
                if start_interp > -1:
                    end_interp = i - 1
            else:
                if start_interp == -1:
                    start_interp = i
            if -1 < start_interp <= end_interp:
                if start_interp == 0:
                    for j in xrange(start_interp, end_interp+1):
                        table_totals[j] = table_totals[end_interp+1]
                        print("start", j, table_totals[j])
                elif end_interp == len(table_totals) - 1:
                    for j in xrange(start_interp, end_interp+1):
                        table_totals[j] = table_totals[start_interp-1]
                        print("end", j, table_totals[j])
                else:
                    start_val = table_totals[start_interp - 1]
                    delta = ((table_totals[end_interp + 1] - start_val) /
                        (end_interp - start_interp + 2))
                    print(start_val, table_totals[end_interp + 1], delta)
                    if delta > 0:
                        for j in xrange(start_interp, end_interp+1):
                            table_totals[j] = start_val + delta*(j - start_interp)
                            print("middle", j, table_totals[j])
                    else:
                        for j in xrange(start_interp, end_interp+1):
                            table_totals[j] = start_val
                            print("middle-fake", j, table_totals[j])

                start_interp = -1
                end_interp = -1
            i += 1


        print("Dumping raw data containing rank, netgain, and netsnow: peras.csv")
        f = open('peras.csv', 'w')
        numweeks = len(peras_data.itervalues().next())
        f.write("week,table_netsnow,cr_netsnow,cr_netgain")
        for asn in peras_data:
            f.write(",as{0}_rank,as{0}_netgain,as{0}_netsnow".format(asn))
        f.write("\n")
        for i in xrange(numweeks):
            if data[i]:
                cr_netsnow = sum((x.netsnow for x in data[i].rank_list))
                cr_netgain = sum((x.netgain for x in data[i].rank_list))
            else:
                cr_netsnow = -1
                cr_netgain = -1
            f.write("{0},{1},{2},{3}".format(i, table_totals[i], cr_netsnow if cr_netsnow > -1 else '', cr_netgain if cr_netgain > -1 else''))
            for asn in peras_data:
                if peras_data[asn][i]:
                    f.write(",{0.rank},{0.netgain},{0.netsnow}".format(
                        peras_data[asn][i]))
                else:
                    f.write(",,,")
            f.write("\n")
        f.close()


        print("Creating dot file: dotfile_out.dot")
        # TODO switch this to RGB colors, and expand list
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
        # ecl from http://www.mvps.org/dmcritchie/excel/colors.htm
        ecl = ['#000000',
        '#FF0000',
        '#00FF00',
        '#0000FF',
        '#FFFF00',
        '#FF00FF',
        '#00FFFF',
        '#800000',
        '#008000',
        '#000080',
        '#808000',
        '#800080',
        '#008080',
        '#C0C0C0',
        '#808080',
        '#9999FF',
        '#993366',
        '#FFFFCC',
        '#CCFFFF',
        '#660066',
        '#FF8080',
        '#0066CC',
        '#CCCCFF',
        '#000080',
        '#FF00FF',
        '#FFFF00',
        '#00FFFF',
        '#800080',
        '#800000',
        '#008080',
        '#0000FF',
        '#00CCFF',
        '#CCFFFF',
        '#CCFFCC',
        '#FFFF99',
        '#99CCFF',
        '#FF99CC',
        '#CC99FF',
        '#FFCC99',
        '#3366FF',
        '#33CCCC',
        '#99CC00',
        '#FFCC00',
        '#FF9900',
        '#FF6600',
        '#666699',
        '#969696',
        '#003366',
        '#339966',
        '#003300',
        '#333300',
        '#993300',
        '#993366',
        '#333399',
        '#333333']
        color_map = {}
        listlen = len(contrast_color_list)
        for i in xrange(len(rwfreq_list)):
            color_map[rwfreq_list[i][0]] = contrast_color_list[i % listlen]

        df = open('dotfile_out.dot', 'w')
        df.write('strict graph {\ngraph[ordering=out, outputorder=edgesfirst, splines=false];\n')
        last_week = -1
        for i in xrange(min(len(data), MAX_WEEKS_PLOT)):
            rows = min(len(data), MAX_WEEKS_PLOT)
            if data[i]:
                df.write('week{0}row0 [label="Week {0}\\n{1}", shape=box, style=filled, fillcolor=white, pos="{2},{3}", pin=true];\n'.format(i, data[i].date, i*COL_SPACE+59, rows*ROW_SPACE+22))
                for r in xrange(min(len(data[i].rank_list), MAX_ROWS_PLOT)):
                    df.write('week{0}row{1} [label="AS {2.asnum}\\n{2.netgain}/{2.netsnow}", shape=ellipse, style=filled, fillcolor=white, pos="{3},{4}", pin=true, color="{5}", penwidth=12];\n'.format(i, r+1, data[i].rank_list[r], i*COL_SPACE+59, (rows-r-1)*ROW_SPACE+22, color_map[data[i].rank_list[r].asnum]))
                    df.write('week{0}row{1} -- week{0}row{2} [style=invis];\n'.format(i, r, r+1))
                    if last_week >= 0:
                        for j in xrange(min(len(data[last_week].rank_list),
                            MAX_ROWS_PLOT)):
                            if data[i].rank_list[r].asnum == data[last_week].rank_list[j].asnum:
                                df.write('week{0}row{1} -- week{2}row{3} [constraint=false, penwidth=12, color="{4}"];'.format(i, r+1, last_week, j+1, color_map[data[i].rank_list[r].asnum]))
                last_week = i
            else:
                df.write('week{0}row0 [label="Week {0}", shape=box, style=filled, fillcolor=tomato, pos="{1},{2}", pin=true];\n'.format(i, i*COL_SPACE+59, rows*ROW_SPACE+22))
        df.write('}\n')
        df.close()

        print("Creating R file: as_plots.r")
        f = open('as_plots.r', 'w')

        f.write(
"""library("zoo")
cidr_report <- read.csv("peras.csv")
pdf("as_plots.pdf", paper="USr", width=10, height=7.5)
par(mfrow=c(20,1), mar=c(0,4,0,0))
""")
        for (asn,wfreq) in wfreq_list:
            f.write('plot(cidr_report$as{0}_rank, xlab="", ylab="{0}",   type="h", ylim=c(0,30), yaxt="n", col="grey")\n'.format(asn))
            f.write('par(new=TRUE)\n')
            f.write('plot(rollapply(zoo(cidr_report$as{0}_netgain/cidr_report$as{0}_netsnow), 4, (mean)), xlab="", ylab="", yaxt="n", xaxt="n",   type="l", ylim=c(0,1), col="red", lwd=2)\n'.format(asn))
            f.write('par(new=TRUE)\n')
            f.write('plot(rollapply(zoo(cidr_report$as{0}_netgain/cidr_report$cr_netgain), 4, (mean)), xlab="", ylab="", yaxt="n", xaxt="n",  type="l", ylim=c(0,1), col="blue", lwd=2)\n'.format(asn))
            f.write('par(new=TRUE)\n')
            f.write('plot(rollapply(zoo(cidr_report$as{0}_netsnow/cidr_report$cr_netsnow), 4, (mean)), xlab="", ylab="", yaxt="n", xaxt="n",  type="l", ylim=c(0,1), col="green", lwd=2)\n'.format(asn))
            f.write('par(new=FALSE)\n')
        f.write("dev.off()\n")
        f.close()

    else:
        print("USAGE: ...")

