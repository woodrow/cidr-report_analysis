UNIX_EPOCH = as.Date('1970-01-01')
DATA_IMAGE_NAME = "_correlation.RData"
CONTROL_MIN_PREFIX_THRESHOLD = 10

EPOCH     = as.Date('1997-11-14')
END_EPOCH = as.Date('2011-01-31')
MIN_RANK  = 0
MAX_RANK  = 29
FILL_NAS  = F

EPOCH = EPOCH - as.POSIXlt(EPOCH)$wday
END_EPOCH = END_EPOCH - as.POSIXlt(END_EPOCH)$wday

get.ecr <- function(min_date=EPOCH, max_date=END_EPOCH, min_rank=MIN_RANK,
    max_rank=MAX_RANK) {
    library(RdbiPgSQL)
    conn <- dbConnect(
        PgSQL(),
        host="mitas-2.csail.mit.edu",
        dbname="woodrow",
        user="woodrow",
        password="woodrow$mitas-2@2011"
    )
    res = dbSendQuery(conn, paste(
        "SELECT date, origin_as, rank",
        "FROM email_cidr_reports",
        "WHERE date BETWEEN '", min_date, "' AND '", max_date, "'",
        "AND rank BETWEEN '", min_rank, "' AND '", max_rank, "'",
        "ORDER BY origin_as, date;"))
    email_cidr_report <<- dbGetResult(res)
    email_cidr_report$date = as.Date(email_cidr_report$date, '%m-%d-%Y')
    ecr = split(email_cidr_report,
        factor(email_cidr_report$origin_as,
        levels=unique(email_cidr_report$origin_as)))
    #EPOCH <<- min(email_cidr_report$date)
    #EPOCH = EPOCH - as.POSIXlt(EPOCH)$wday
    #EPOCH = EPOCH - 7  # bring it back one week before
    dbDisconnect(conn)
    return(ecr)
}

preprocess.ecr <- function(ecr, min_date=EPOCH, max_date=END_EPOCH) {
    dates = as.Date(seq(as.numeric(EPOCH), as.numeric(END_EPOCH)),
        origin=UNIX_EPOCH)
    weeks = seq(1, ceiling((END_EPOCH-EPOCH)/7))
    date_weeks = as.Date((weeks-1)*7, origin=EPOCH)
    cecr = list()#(weeks=date_weeks)  # canonical ECR, by week
    for(origin_as in names(ecr)) {
        cecr[[origin_as]] = rep(NA, length(weeks))
        for(ri in c(1:nrow(ecr[[origin_as]]))) {
            row = ecr[[origin_as]][ri,]
            cecr[[origin_as]][ceiling((row$date-EPOCH)/7)] = row$rank
        }
    }
    # fill in the blanks
    available_dates = rep(F, length(weeks))
    for(d in unique(as.Date(email_cidr_report$date, '%m-%d-%Y'))) {
        available_dates[ceiling((as.Date(d, origin=UNIX_EPOCH)-EPOCH)/7)] = T
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
                    appearances[['date_index']][apcount] = start
                    appearances[['duration']][apcount] = duration
                    duration = 0
                    start = 0
                }
            }
        }
    }
    # handle the last partially-complete appearance
    if(start > 0) {
        apcount = apcount + 1
        appearances[['date']][apcount] = dates[start]
        appearances[['date_index']][apcount] = start
        appearances[['duration']][apcount] = duration
        duration = 0
        start = 0
    }

    if(apcount > 0) {
        appearances[['date']] = as.Date(appearances[['date']], UNIX_EPOCH)
        return(appearances)
    } else {
        return(NA)
    }
}


is.trulytrue <- function(x) {
    return(x == T & !is.na(x))
}


get.control.gcr <- function(ecr_ases, min_date=EPOCH, max_date=END_EPOCH) {
    max_date = max_date + 730
    library(RdbiPgSQL)
    conn <- dbConnect(
        PgSQL(),
        host="mitas-2.csail.mit.edu",
        dbname="woodrow",
        user="woodrow",
        password="woodrow$mitas-2@2011"
    )

#    print(paste(
#        "SELECT tmp.origin_as, tmp.datemin, tmp.datemax",
#        "FROM (",
#        "    SELECT origin_as, min(date) as datemin, max(date) as datemax",
#        "    FROM gen_cidr_reports",
#        "    WHERE id >= 12415379",
#        "    AND nets_current > ", CONTROL_MIN_PREFIX_THRESHOLD,
#        "    AND date BETWEEN '", min_date, "' AND '", max_date, "'",
#        "    AND origin_as not in (",
#        "        SELECT origin_as",
#        "        FROM email_cidr_reports",
#        "        WHERE date BETWEEN '", min_date, "' AND '", max_date, "'",
#        "        GROUP BY origin_as",
#        "        ORDER BY origin_as",
#        "        )",
#        "    AND origin_as > 0",
#        "    GROUP BY origin_as",
#        "    ORDER BY origin_as, datemin",
#        ") as tmp",
#        "WHERE (tmp.datemax - tmp.datemin) >= 730",
#        "ORDER BY origin_as, datemin;"))
#    dbDisconnect(conn)
#    return()

    res = dbSendQuery(conn, paste(
        "SELECT tmp.origin_as, tmp.datemin, tmp.datemax",
        "FROM (",
        "    SELECT origin_as, min(date) as datemin, max(date) as datemax",
        "    FROM gen_cidr_reports",
        "    WHERE id >= 12415379",
        "    AND nets_current > ", CONTROL_MIN_PREFIX_THRESHOLD,
        "    AND date BETWEEN '", min_date, "' AND '", max_date, "'",
        "    AND origin_as not in (",
        "        SELECT origin_as",
        "        FROM email_cidr_reports",
        "        WHERE date BETWEEN '", min_date, "' AND '", max_date, "'",
        "        GROUP BY origin_as",
        "        ORDER BY origin_as",
        "        )",
        "    AND origin_as > 0",
        "    GROUP BY origin_as",
        "    ORDER BY origin_as, datemin",
        ") as tmp",
        "WHERE (tmp.datemax - tmp.datemin) >= 730",
        "ORDER BY origin_as, datemin;"))
    control_candidates = dbGetResult(res)
    print('progress1')

    candidate_ases = control_candidates$origin_as[
        sample(1:length(control_candidates$origin_as), length(ecr_ases))]

#    print(paste(
#    "SELECT date, origin_as, rank_netgain, rank_netsnow,",
#        "nets_reduced as netgain, nets_current as netsnow",
#    "FROM gen_cidr_reports",
#    "WHERE id >= 12415379",
#    "AND origin_as in (", paste(candidate_ases, collapse=","), ")",
#    "ORDER BY origin_as, date;"))
#    dbDisconnect(conn)
#    return()

    res = dbSendQuery(conn, paste(
        "SELECT date, origin_as, rank_netgain, rank_netsnow,",
            "nets_reduced as netgain, nets_current as netsnow",
        "FROM gen_cidr_reports",
        "WHERE id >= 12415379",
        "AND date BETWEEN '", min_date, "' AND '", max_date, "'",
        "AND origin_as in (", paste(candidate_ases, collapse=","), ")",
        "ORDER BY origin_as, date;"))
    control_gen_cidr_report <<- dbGetResult(res)
    control_gen_cidr_report$date = as.Date(
        control_gen_cidr_report$date, '%m-%d-%Y')
    congcr = split(control_gen_cidr_report,
        factor(control_gen_cidr_report$origin_as,
        levels=unique(control_gen_cidr_report$origin_as)))

    dbDisconnect(conn)
    return(congcr)
}


get.gcr <- function(origin_ases, min_date=EPOCH, max_date=END_EPOCH) {
    max_date = max_date + 730
    library(RdbiPgSQL)
    conn <- dbConnect(
        PgSQL(),
        host="mitas-2.csail.mit.edu",
        dbname="woodrow",
        user="woodrow",
        password="woodrow$mitas-2@2011"
    )
    res = dbSendQuery(conn, paste(
        "SELECT date, origin_as, rank_netgain, rank_netsnow,",
            "nets_reduced as netgain, nets_current as netsnow",
        "FROM gen_cidr_reports",
        "WHERE id >= 12415379",
        "AND date BETWEEN '", min_date, "' AND '", max_date, "'",
        "AND origin_as in (", paste(origin_ases, collapse=","), ")",
        "ORDER BY origin_as, date;"))
    gen_cidr_report <<- dbGetResult(res)
    gen_cidr_report$date = as.Date(gen_cidr_report$date, '%m-%d-%Y')
    gcr = split(gen_cidr_report,
        factor(gen_cidr_report$origin_as,
        levels=unique(gen_cidr_report$origin_as)))
    dbDisconnect(conn)
    return(gcr)
}


preprocess.gcr <- function(gcr, no_nas=F) {
    END_EPOCH = END_EPOCH + 730
    dates = as.Date(seq(as.numeric(EPOCH), as.numeric(END_EPOCH)),
        origin=UNIX_EPOCH)
    weeks = seq(1, ceiling((END_EPOCH-EPOCH)/7))
    date_weeks = as.Date((weeks-1)*7, origin=EPOCH)
    cgcr = list()#(weeks=date_weeks)  # canonical ECR, by week
    for(origin_as in names(gcr)) {
        print(origin_as)
        if(no_nas) {
            as_data = data.frame(
                rank_netgain=rep(999999,length(weeks)),
                rank_netsnow=rep(999999,length(weeks)),
                netgain=rep(0,length(weeks)),
                netsnow=rep(0,length(weeks)))
        } else {
            as_data = data.frame(
                rank_netgain=as.integer(NA),
                rank_netsnow=as.integer(NA),
                netgain=as.integer(NA),
                netsnow=as.integer(NA))[rep(NA,length(weeks)),]
        }
        for(ri in c(1:nrow(gcr[[origin_as]]))) {
            row = gcr[[origin_as]][ri,]
            as_data[ceiling((row$date-EPOCH)/7),] = row[3:6]
        }
        cgcr[[origin_as]] = as_data
    }
    # fill in the blanks
    available_dates = rep(F, length(weeks))
    for(d in unique(as.Date(gen_cidr_report$date, '%m-%d-%Y'))) {
        available_dates[ceiling((as.Date(d, origin=UNIX_EPOCH)-EPOCH)/7)] = T
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


load.data <- function() {
    print("loading email cidr report data")
    print(Sys.time())
    ecr = get.ecr()
    cecr <<- preprocess.ecr(ecr)
    print(Sys.time())

    print("constructing appearances list")
    print(Sys.time())
    appearances = list()
    for(origin_as in names(cecr)) {
        appearance = find.appearances(
            cecr[[origin_as]], cecr[['weeks']])
        if(length(appearance) > 1 || !is.na(appearance)) {
            appearances[[origin_as]] = appearance
        }
    }
    appearances <<- appearances
    print(Sys.time())

    print("loading generated cidr report data")
    print(Sys.time())
    gcr <<- get.gcr(
        names(appearances)[is.trulytrue(as.integer(names(appearances)) > 0)])
    print(Sys.time())
    cgcr <<- preprocess.gcr(gcr, no_nas=FILL_NAS)
    print(Sys.time())

    print("loading control gen cidr report data")
    print(Sys.time())
    congcr <<- get.control.gcr(
        names(appearances)[is.trulytrue(as.integer(names(appearances)) > 0)])
    print(Sys.time())
    concgcr <<- preprocess.gcr(congcr, no_nas=FILL_NAS)
    print(Sys.time())

    print("data load complete")
    data_loaded <<- T
}

fill.NAs <- function(vec, fillval) {
    for(i in c(1:length(vec))) {
        if(is.na(vec[i])) {
            vec[i] = fillval
        }
    }
    return(vec)
}

do.stuff <- function(reload=F) {
    DATA_IMAGE_NAME = paste("_",
        EPOCH, "_",
        END_EPOCH, "_",
        MIN_RANK, "_",
        MAX_RANK, "_",
        FILL_NAS, "_",
        DATA_IMAGE_NAME, sep="")
    if(!exists('data_loaded') || !data_loaded) {
        if(!reload && file_test('-f', DATA_IMAGE_NAME)) {
            load(DATA_IMAGE_NAME, .GlobalEnv)
            print("data loaded from RData file")
        } else {
            load.data()
            save.image(DATA_IMAGE_NAME)
            print("data saved to RData file")
        }
    }
    print("ready")

    row_delta_days = c(30, 60, 90, 180, 365, 547, 730)
    row_names = c("initial", paste("delta_", row_delta_days, sep=""))

    as_deltas = list()
    total_appearances = 0

    for (origin_as in
        names(appearances)[is.trulytrue(as.integer(names(appearances)) > 0)]) {
        appearance_list = amalgamate.appearances(appearances[[origin_as]])
        appearance_deltas = list()
        ad_index = 1
        for(i in c(1:length(appearance_list$date))) {
            if(!is.na(appearance_list$date_index[i])) {
                idx = appearance_list$date_index[i]
                deltas = data.frame(
                    rank_netgain=rep(NA,length(row_names)),
                    rank_netsnow=rep(NA,length(row_names)),
                    netgain=rep(NA,length(row_names)),
                    netsnow=rep(NA,length(row_names)),
                    weeknum=rep(NA,length(row_names)),
                    row.names=row_names
                )
                deltas['initial',][1:4] = cgcr[[origin_as]][idx,]
                deltas['initial',]$weeknum = idx
                for(d in row_delta_days) {
                    dw = round(d/7)
                    rn = paste("delta_", d, sep="")
                    deltas[rn,][1:4] = (
                        cgcr[[origin_as]][idx+dw,] - deltas['initial',][1:4])
                    deltas[rn,]$weeknum = dw
                }
                appearance_deltas[[ad_index]] = deltas
                ad_index = ad_index + 1
                total_appearances = total_appearances + 1
            }
        }
        as_deltas[[origin_as]] = appearance_deltas
    }
    as_deltas <<- as_deltas

    delta_dists = list()
    for (colname in  paste("delta_", row_delta_days, sep="")) {
        delta_dists[[colname]] = data.frame(
            rank_netgain = rep(NA,total_appearances),
            rank_netsnow = rep(NA,total_appearances),
            netgain      = rep(NA,total_appearances),
            netsnow      = rep(NA,total_appearances),
            weeknum      = rep(NA,total_appearances),
            origin_as    = rep(NA,total_appearances),
            rel_netgain  = rep(NA,total_appearances),
            rel_netsnow  = rep(NA,total_appearances),
            frac_deagg   = rep(NA,total_appearances)
        )
    }

    aix = 1
    for(origin_as in names(as_deltas)) {
        for(ai in c(1:length(as_deltas[[origin_as]]))) {
            for (colname in paste("delta_", row_delta_days, sep="")) {
                delta_dists[[colname]][aix,][1:5] = (
                    as_deltas[[origin_as]][[ai]][colname,])
                delta_dists[[colname]][aix,]$origin_as = as.integer(origin_as)
                delta_dists[[colname]][aix,]$rel_netgain = (
                    as_deltas[[origin_as]][[ai]][colname,]$netgain /
                    as_deltas[[origin_as]][[ai]]['initial',]$netgain)
                delta_dists[[colname]][aix,]$rel_netsnow = (
                    as_deltas[[origin_as]][[ai]][colname,]$netsnow /
                    as_deltas[[origin_as]][[ai]]['initial',]$netsnow)
                delta_dists[[colname]][aix,]$frac_deagg = ((
                    as_deltas[[origin_as]][[ai]][colname,]$netgain +
                    as_deltas[[origin_as]][[ai]]['initial',]$netgain) / (
                    as_deltas[[origin_as]][[ai]][colname,]$netsnow +
                    as_deltas[[origin_as]][[ai]]['initial',]$netsnow))
            }
            aix = aix + 1
        }
    }

    delta_dists <<- delta_dists

    ############################################################################
    # CONTROL
    # need to generate appearances randomly from within range



    as_deltas = list()
    total_appearances = 0

    for (origin_as in
        names(appearances)[is.trulytrue(as.integer(names(appearances)) > 0)]) {
        appearance_list = amalgamate.appearances(appearances[[origin_as]])
        appearance_deltas = list()
        ad_index = 1
        for(i in c(1:length(appearance_list$date))) {
            if(!is.na(appearance_list$date_index[i])) {
                idx = appearance_list$date_index[i]
                deltas = data.frame(
                    rank_netgain=rep(NA,length(row_names)),
                    rank_netsnow=rep(NA,length(row_names)),
                    netgain=rep(NA,length(row_names)),
                    netsnow=rep(NA,length(row_names)),
                    weeknum=rep(NA,length(row_names)),
                    row.names=row_names
                )
                deltas['initial',][1:4] = cgcr[[origin_as]][idx,]
                deltas['initial',]$weeknum = idx
                for(d in row_delta_days) {
                    dw = round(d/7)
                    rn = paste("delta_", d, sep="")
                    deltas[rn,][1:4] = (
                        cgcr[[origin_as]][idx+dw,] - deltas['initial',][1:4])
                    deltas[rn,]$weeknum = dw
                }
                appearance_deltas[[ad_index]] = deltas
                ad_index = ad_index + 1
                total_appearances = total_appearances + 1
            }
        }
        as_deltas[[origin_as]] = appearance_deltas
    }
    as_deltas <<- as_deltas

    delta_dists = list()
    for (colname in  paste("delta_", row_delta_days, sep="")) {
        delta_dists[[colname]] = data.frame(
            rank_netgain = rep(NA,total_appearances),
            rank_netsnow = rep(NA,total_appearances),
            netgain      = rep(NA,total_appearances),
            netsnow      = rep(NA,total_appearances),
            weeknum      = rep(NA,total_appearances),
            origin_as    = rep(NA,total_appearances),
            rel_netgain  = rep(NA,total_appearances),
            rel_netsnow  = rep(NA,total_appearances),
            frac_deagg   = rep(NA,total_appearances)
        )
    }

    aix = 1
    for(origin_as in names(as_deltas)) {
        for(ai in c(1:length(as_deltas[[origin_as]]))) {
            for (colname in paste("delta_", row_delta_days, sep="")) {
                delta_dists[[colname]][aix,][1:5] = (
                    as_deltas[[origin_as]][[ai]][colname,])
                delta_dists[[colname]][aix,]$origin_as = as.integer(origin_as)
                delta_dists[[colname]][aix,]$rel_netgain = (
                    as_deltas[[origin_as]][[ai]][colname,]$netgain /
                    as_deltas[[origin_as]][[ai]]['initial',]$netgain)
                delta_dists[[colname]][aix,]$rel_netsnow = (
                    as_deltas[[origin_as]][[ai]][colname,]$netsnow /
                    as_deltas[[origin_as]][[ai]]['initial',]$netsnow)
                delta_dists[[colname]][aix,]$frac_deagg = ((
                    as_deltas[[origin_as]][[ai]][colname,]$netgain +
                    as_deltas[[origin_as]][[ai]]['initial',]$netgain) / (
                    as_deltas[[origin_as]][[ai]][colname,]$netsnow +
                    as_deltas[[origin_as]][[ai]]['initial',]$netsnow))
            }
            aix = aix + 1
        }
    }

    delta_dists <<- delta_dists

}


plot.densities <- function(typename='netgain') {
#    densities = list()
#    xlims = c(0,0)
#    ylims = c(0,0)
#    for(name in names(delta_dists)) {
#        d = density(
#        delta_dists[[name]]$rel_netsnow[!is.na(delta_dists[[name]]$rel_netsnow)])
#        densities[[name]] = d
#        xlims = c(min(xlims, d$x), max(xlims, d$x))
#        ylims = c(min(ylims, d$y), max(ylims, d$y))
#    }
#    xlims=c(-5,5)
#    print(xlims)
#    print(ylims)
#    ylims[1] = ylims[1] + 1e-20
#    colors = rainbow(7)
#    index = 1
#    for(name in names(densities)) {
#        plot(densities[[name]], xlim=xlims, ylim=ylims, col=colors[index])
#        par(new=T)
#        index = index + 1
#    }
#    legend(
#        'topright',
#        names(densities),
#        col=colors,
#        lty=1,
#        lwd=1,
#        bg="white",
#        inset=0.02
#    )

#    x11() #####################################################################
    cdfs = list()
    xlims = c(0,0)
    #ylims = c(0,0)
    for(name in names(delta_dists)) {
        cdf = ecdf(
        delta_dists[[name]][[typename]][!is.na(delta_dists[[name]][[typename]])])
        cdfs[[name]] = cdf
        xlims = c(min(xlims, knots(cdf)), max(xlims, knots(cdf)))
    }
    #xlims=c(-2000,2000)
    print(xlims)
    #print(ylims)
    #ylims[1] = ylims[1] + 1e-20
    colors = rainbow(7)
    index = 1
    for(name in names(cdfs)) {
        plot(cdfs[[name]], col=colors[index], xlim=xlims)
        par(new=T)
        index = index + 1
    }
    legend(
        'bottomright',
        names(cdfs),
        col=colors,
        lty=1,
        lwd=1,
        bg="white",
        inset=0.02
    )


    ####################################################################
    ## NEXT STEPS; PLOT OTHER FACTORS AND PLOT RELATIVE (%AGE) MEASURES
}

amalgamate.appearances <- function(appearance_list) {
    if (length(appearance_list$date) > 1) {
        last_date = appearance_list$date[1]
        for(i in c(2:length(appearance_list$date))) {
            if((appearance_list$date[i] - last_date) < 730) {
                appearance_list$date[i] = NA
                appearance_list$date_index[i] = NA
                appearance_list$duration[i] = NA
            } else {
                last_date = appearance_list$date[i]
            }
        }
    }
    return(appearance_list)
}


# 1. amalgamate appearances overlapping within 1-2 years?
# 2. for each appearance, collect and store deltas in a structure like
#    deltas[['701']][1,]${delta_30, delta_60, delta_90, delta_180, delta_365, delta_547, delta_730}
# 3. iterate through and collect into an array, and then plot



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
