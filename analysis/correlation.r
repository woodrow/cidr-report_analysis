data_sets = c("email_cidr_report")
for(e in data_sets) {
    if(!exists(e)) {
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
        email_cidr_report = dbGetResult(res)
        email_cidr_report$date = as.Date(email_cidr_report$date, '%m-%d-%Y')
        ecr = split(email_cidr_report,
                factor(email_cidr_report$origin_as, levels=unique(email_cidr_report$origin_as)))
        epoch = min(email_cidr_report$date)
        epoch = epoch - as.POSIXlt(epoch)$wday
        epoch = epoch - 7  # bring it back one week before
        end_epoch = as.Date('2011-01-31')
        ########################################################################
        dbDisconnect(conn)
        break
    }
}

preprocess.ecr <- function() {
    MAGIC_NA = 100
    dates = as.Date(seq(as.numeric(epoch), as.numeric(end_epoch)),
        origin='1970-01-01')
    weeks = seq(1, ceiling((end_epoch-epoch)/7))
    date_weeks = as.Date((weeks-1)*7, origin=epoch)
    cecr = list()#(weeks=date_weeks)  # canonical ECR, by week
    for(origin_as in names(ecr)) {
        cecr[[origin_as]] = rep(MAGIC_NA, length(weeks))
        for(ri in c(1:nrow(ecr[[origin_as]]))) {
            row = ecr[[origin_as]][ri,]
            cecr[[origin_as]][ceiling((row$date-epoch)/7)] = row$rank
        }
    }
    # fill in the blanks
    available_dates = rep(F, length(weeks))
    for(d in unique(email_cidr_report$date)) {
        available_dates[ceiling((as.Date(d, origin='1970-01-01')-epoch)/7)] = T
    }
    for(origin_as in names(cecr)) {
        last_val = MAGIC_NA
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
        if(pattern[i] < 30) {
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
    appearances[['date']] = as.Date(appearances[['date']], '1970-01-01')
    return(appearances)
}

do.stuff <- function() {
    if(!exists('cecr')) {
        cecr = preprocess.ecr()
    }
    appearances = list()
    for(origin_as in names(cecr)) {
        appearances[[origin_as]] = find.appearances(cecr[[origin_as]])
    }

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
