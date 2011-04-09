UNIX_EPOCH = as.Date('1970-01-01')

get.ecr <- function() {
    library(RdbiPgSQL)
    conn <- dbConnect(
        PgSQL(),
        host="mitas-2.csail.mit.edu",
        dbname="woodrow",
        user="woodrow",
        password="woodrow$mitas-2@2011"
    )
    ########################################################################
    res = dbSendQuery(conn, paste(
        "SELECT date, origin_as, rank",
        "FROM email_cidr_reports",
        "ORDER BY origin_as, date;"))
    email_cidr_report <<- dbGetResult(res)
    email_cidr_report$date = as.Date(email_cidr_report$date, '%m-%d-%Y')
    ecr = split(email_cidr_report,
            factor(email_cidr_report$origin_as, levels=unique(email_cidr_report$origin_as)))
    epoch <<- min(email_cidr_report$date)
    epoch = epoch - as.POSIXlt(epoch)$wday
    epoch = epoch - 7  # bring it back one week before
    end_epoch <<- as.Date('2011-01-31')
    ########################################################################
    dbDisconnect(conn)
    return(ecr)
}

preprocess.ecr <- function(ecr) {
    dates = as.Date(seq(as.numeric(epoch), as.numeric(end_epoch)),
        origin=UNIX_EPOCH)
    weeks = seq(1, ceiling((end_epoch-epoch)/7))
    date_weeks = as.Date((weeks-1)*7, origin=epoch)
    cecr = list()#(weeks=date_weeks)  # canonical ECR, by week
    for(origin_as in names(ecr)) {
        cecr[[origin_as]] = rep(NA, length(weeks))
        for(ri in c(1:nrow(ecr[[origin_as]]))) {
            row = ecr[[origin_as]][ri,]
            cecr[[origin_as]][ceiling((row$date-epoch)/7)] = row$rank
        }
    }
    # fill in the blanks
    available_dates = rep(F, length(weeks))
    for(d in unique(as.Date(email_cidr_report$date, '%m-%d-%Y'))) {
        available_dates[ceiling((as.Date(d, origin=UNIX_EPOCH)-epoch)/7)] = T
    }
    for(origin_as in names(cecr)) {
        last_val = NA
        for(ri in c(1:length(cecr[[origin_as]]))) {
            if(available_dates[ri] == F) {
                cecr[[origin_as]][ri] = last_val
            }
            last_val = cecr[[origin_as]][ri]
        }
    }
    cecr[['weeks']] = date_weeks
    return(cecr)
}


find.appearances <- function(pattern, dates) {
    win_width = 4
    max_gap = 8

    appearances = list()
    apcount = 0

    start = 0
    duration = 0
    gap_duration = 0
    for(i in c(1:length(pattern))) {
        if(!is.na(pattern[i])) {
            if(start == 0) {
                start = i
            }
            duration = duration + 1
            gap_duration = 0
        } else {
            if(gap_duration < max_gap) {
                gap_duration = gap_duration + 1
            } else {
                if(start > 0) {
                    apcount = apcount + 1
                    appearances[['date']][apcount] = dates[start]
                    appearances[['duration']][apcount] = duration
                    duration = 0
                    start = 0
                }
            }
        }
    }

    if(apcount > 0) {
        appearances[['date']] = as.Date(appearances[['date']], UNIX_EPOCH)
        return(appearances)
    } else {
        return(NA)
    }
}


is.nottrue <- function(x) {
    (x == T)[!is.na(x==T)]
}


get.gcr <- function(origin_ases) {
    library(RdbiPgSQL)
    conn <- dbConnect(
        PgSQL(),
        host="mitas-2.csail.mit.edu",
        dbname="woodrow",
        user="woodrow",
        password="woodrow$mitas-2@2011"
    )
    ########################################################################
    res = dbSendQuery(conn, paste(
        "SELECT date, origin_as, rank_netgain, rank_netsnow,",
            "nets_current, nets_reduced",
        "FROM gen_cidr_reports",
        "WHERE id >= 12415379",
        "AND origin_as in (", paste(origin_ases, collapse=","), ")",
        "ORDER BY origin_as, date;"))
    gen_cidr_report <<- dbGetResult(res)
    gen_cidr_report$date = as.Date(gen_cidr_report$date, '%m-%d-%Y')
    gcr = split(gen_cidr_report,
        factor(gen_cidr_report$origin_as,
        levels=unique(gen_cidr_report$origin_as)))
    ########################################################################
    dbDisconnect(conn)
    return(gcr)
}

################################################################################
################################################################################
# NOTES TO SELF
#
# - USE DATA FRAMES INSTEAD OF LISTS TO ALLOW ROW INDEXING
#
################################################################################
################################################################################

preprocess.gcr <- function(gcr) {
    dates = as.Date(seq(as.numeric(epoch), as.numeric(end_epoch)),
        origin=UNIX_EPOCH)
    weeks = seq(1, ceiling((end_epoch-epoch)/7))
    date_weeks = as.Date((weeks-1)*7, origin=epoch)
    cgcr = list()#(weeks=date_weeks)  # canonical ECR, by week
    for(origin_as in names(gcr)) {
        print(origin_as)
        as_data = data.frame(
            rank_netgain=as.integer(NA),
            rank_netsnow=as.integer(NA),
            netsnow=as.integer(NA),
            netgain=as.integer(NA))[rep(NA,length(weeks)),]
        for(ri in c(1:nrow(gcr[[origin_as]]))) {
            row = gcr[[origin_as]][ri,]
            as_data[ceiling((row$date-epoch)/7),] = row[3:6]
        }
        cgcr[[origin_as]] = as_data
    }
    # fill in the blanks
    available_dates = rep(F, length(weeks))
    for(d in unique(as.Date(gen_cidr_report$date, '%m-%d-%Y'))) {
        available_dates[ceiling((as.Date(d, origin='1970-01-01')-epoch)/7)] = T
    }
    for(origin_as in names(cgcr)) {
        last_row = rep(NA, 4)
        for(ri in c(1:nrow(cgcr[[origin_as]]))) {
            if(available_dates[ri] == F) {
                cgcr[[origin_as]][ri,] = last_row
            }
            last_row = cgcr[[origin_as]][ri,]
        }
    }
    cgcr[['weeks']] = date_weeks
    return(cgcr)
}

do.stuff <- function() {
    print("cecr")
    if(!exists('cecr')) {
        ecr = get.ecr()
        cecr <<- preprocess.ecr(ecr)
    }
    print("cecr done")
    print("appearances")
    if(!exists('appearances')) {
        appearances = list()
        for(origin_as in names(cecr)) {
            appearance = find.appearances(
                cecr[[origin_as]], cecr[['weeks']])
            if(length(appearance) > 1 || !is.na(appearance)) {
                appearances[[origin_as]] = appearance
            }
        }
        appearances <<- appearances
    }
    print("appearances done")
    print("cgcr")
    if(!exists('cgcr')) {
        gcr <<- get.gcr(
            names(appearances)[is.nottrue(as.integer(names(appearances)) > 0)])
        cgcr <<- preprocess.gcr(gcr)
    }
    print("cgcr done")
    # extract.data(appearances, cgcr)
}



corr.plot <- function(v, weeks) {
    plot.appearances(1*(v<30), weeks)

}


rotleft <- function(v, k=1) {
    v[(k:(length(v)+k-1))%%length(v) + 1]
}


plot.appearances <- function(pattern, date_axis) {
    win_width = 4
    max_gap = 0
    window = rep(1, win_width)
    eps = 1e-9

    corr = convolve(pattern, window, conj=T, type="open")
    corr_hits = rotleft((corr >= (win_width-eps)), win_width-1)
    corr_diff = rotleft(diff(corr_hits), -1)
    corr_diff = (corr_diff > 0)

    plot_subjects = list(
        pattern,
#        corr,
        corr_hits,
        corr_diff
        )

    #ylims = c(min(sapply(plot_subjects, min)), max(sapply(plot_subjects, max)))
    ylims = c(-1,1)
    #xlims = c(0, max(sapply(plot_subjects, length)))
    #xlims = c(as.Date('1996-01-01'),as.Date('2000-01-01'))
    xlims = c(min(date_axis), max(date_axis))
    #xlims = c(min(date_axis), as.Date('2005-01-01'))

#    plot(
#    date_axis,
#    corr[1:length(date_axis)],
#    type='s',
#    col='orange',
#    xlim=xlims,
#    ylim=ylims, xaxt='n', yaxt='n', lwd=2)
#    par(new=T)
    plot(
        date_axis,
        -1*corr_hits[1:length(date_axis)],
        type='s',
        col='red',
        xlim=xlims,
        ylim=ylims, xaxt='n', yaxt='n', lwd=2)
    par(new=T)
    plot(
        date_axis,
        -1*corr_diff[1:length(date_axis)],
        type='s',
        col='green',
        xlim=xlims,
        ylim=ylims, xaxt='n', yaxt='n', lwd=2)
    par(new=T)
    plot(
        date_axis,
        pattern,
        type='h',
        col='black',
        xlim=xlims,
        ylim=ylims, lwd=1)

    print(date_axis[corr_diff[1:length(date_axis)]])
}
