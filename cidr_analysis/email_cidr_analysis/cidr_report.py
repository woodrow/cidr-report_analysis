import collections
import datetime
import re
import psycopg2


NANOG_EPOCH = datetime.date(1996, 9, 13) #datetime.date(2000, 12, 22)


CRRow = collections.namedtuple('CRRow',
    'asnum netsnow netsaggr netgain rank netname')
CidrReport = collections.namedtuple('CRWeek',
    'date week file table_total rank_list')


def parse_report(infile, epoch=NANOG_EPOCH):
    infile_text = ''.join(infile.readlines())
    table_search = re.search(
        '--- (\d{2}\S{3}\d{2}) ---'
        '.*?\n(.*?)'
        '(?:\n\n\n|\n\n[^\n]*--- (\d{2}\S{3}\d{2}) ---)',
        infile_text, re.I|re.M|re.S)
    table = table_search.groups()[1].split('\n')
    date = datetime.datetime.strptime(table_search.groups()[0], '%d%b%y').date()
    week = (date - epoch).days // 7
    rank = 0
    table_total_row = None
    rank_list = [None]*30
    for line in table:
        components = line.split()
        if len(components) > 0:
            if re.match('AS\d+', components[0]):
                assert rank < 30
                rank_list[rank] = CRRow(asnum=int(components[0][2:]),
                    netsnow=int(components[1]), netsaggr=int(components[2]),
                    netgain=int(components[3]), rank=rank,
                    netname=' '.join(components[5:]))
                rank += 1
            else:
                if re.match('^Table', components[0]):
                    table_total_row = CRRow(asnum=None,
                    netsnow=int(components[1]), netsaggr=int(components[2]),
                    netgain=int(components[3]), rank=None, netname='Table')
    assert rank == 30
    return CidrReport(date, week, infile.name, table_total_row, rank_list)


def parse_reports(file_paths=[]):
    num_weeks = ((datetime.date(2011, 01, 31) - NANOG_EPOCH).days // 7) + 1
    data = [None]*num_weeks
    peras_data = collections.defaultdict(lambda: [None]*num_weeks)
    dup_count = 0
    for fp in file_paths:
        f = open(fp)
        cidr_report = parse_report(f, NANOG_EPOCH)
        week = cidr_report.week
        if not data[week]:
            data[week] = cidr_report
            for row in data[week].rank_list:
                peras_data[row.asnum][week] = row
        else:
            dup_count += 1
            print("DUPLICATE DATA for week {0}".format(week))
            print("    existing:\n    date: {0}\n    file: {1}".format(
                data[week].date, data[week].file))
            print("    new:\n    date: {0}\n    file: {1}".format(
                cidr_report.date, cidr_report.file))
        f.close()
    if dup_count:
        print("-----\nTOTAL DUPES: {0}\n-----".format(dup_count))
    return (data, peras_data)


def get_from_db(date, conn, epoch=NANOG_EPOCH):
    cursor = conn.cursor()
    cursor.execute((
        'SELECT origin_as, netsnow, netgain, rank, netname '
        'FROM email_cidr_reports '
        'WHERE date = %s'), (date.isoformat(),))
    results = cursor.fetchall()

    if len(results) == 0:
        raise ValueError("Zero results returned")
    row_list = []
    table_total = None
    for row in results:
        cr_row = CRRow(row[0], row[1], row[1] - row[2], row[2], row[3], row[4])
        if cr_row.asnum == -3:  # magic table_total ASN
            table_total = cr_row
        else:
            row_list.append(cr_row)
    row_list.sort(key=lambda x: x.rank)
    return CidrReport(
        date=date,
        week=(date - epoch).days // 7,
        file='postgres',
        table_total=table_total,
        rank_list=row_list
        )


def add_to_db(data, conn):
    cursor = conn.cursor()
    for week in data:
        if week:
            for row in week.rank_list:
                cursor.execute(
                    ('INSERT INTO email_cidr_reports (date, '
                     'origin_as, rank, netsnow, netgain, netname, insert_date) '
                     'VALUES (%s, %s, %s, %s, %s, %s, %s)'),
                    (week.date, row.asnum, row.rank, row.netsnow, row.netgain,
                        row.netname, datetime.datetime.utcnow().isoformat(' ')))
            if week.table_total:
                row = week.table_total
                cursor.execute(
                    ('INSERT INTO email_cidr_reports (date, '
                     'origin_as, rank, netsnow, netgain, netname, insert_date) '
                     'VALUES (%s, %s, %s, %s, %s, %s, %s)'),
                    (week.date, -3, 0, row.netsnow, row.netgain, row.netname,
                        datetime.datetime.utcnow().isoformat(' ')))
                    # magic as -3 = total
            conn.commit()

