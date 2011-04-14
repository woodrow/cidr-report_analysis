#!/usr/bin/python

dates = [('1997-11-14', '2011-01-30')
         ('1997-11-14', '2000-12-31'),
         ('2001-01-01', '2003-12-31'),
         ('2004-01-01', '2006-12-31'),
         ('2007-01-01', '2009-12-31')]
ranks = [(0,9), (10,19), (20,29)]
fill = ['F']#, 'T']

filecount = 1

for fill_val in fill:
    for d in dates:
        f = open('corr_input_{0}.r'.format(filecount), 'w')
        f.write("source('correlation.r')\n")
        f.write("EPOCH     = as.Date('{0}')\n".format(d[0]))
        f.write("END_EPOCH = as.Date('{0}')\n".format(d[1]))
        f.write("MIN_RANK  = {0}\n".format(0))
        f.write("MAX_RANK  = {0}\n".format(29))
        f.write("FILL_NAS  = {0}\n".format(fill_val))
        f.write("EPOCH = EPOCH - as.POSIXlt(EPOCH)$wday\n" 
                "END_EPOCH = END_EPOCH - as.POSIXlt(END_EPOCH)$wday\n")
        f.write("do.stuff(reload=T)\n")
        f.write("quit(save='no')\n")
        f.close()
        filecount += 1

for fill_val in fill:
    for r in ranks:
        f = open('corr_input_{0}.r'.format(filecount), 'w')
        f.write("source('correlation.r')\n")
        f.write("EPOCH     = as.Date('{0}')\n".format('1997-11-14'))
        f.write("END_EPOCH = as.Date('{0}')\n".format('2011-01-30'))
        f.write("MIN_RANK  = {0}\n".format(r[0]))
        f.write("MAX_RANK  = {0}\n".format(r[1]))
        f.write("FILL_NAS  = {0}\n".format(fill_val))
        f.write("EPOCH = EPOCH - as.POSIXlt(EPOCH)$wday\n" 
                "END_EPOCH = END_EPOCH - as.POSIXlt(END_EPOCH)$wday\n")
        f.write("do.stuff(reload=T)\n")
        f.write("quit(save='no')\n")
        f.close()
        filecount += 1
