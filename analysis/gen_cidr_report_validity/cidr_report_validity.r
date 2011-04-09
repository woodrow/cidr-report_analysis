if(!exists('cidr.compare')) {
    cidr.compare = read.csv("cidr_report_compare_newagg.csv",
        colClasses=c(
        "Date",     # date
        "integer",  # week
        "integer",  # delta_netsnow_top30
        "integer",  # gcr_greater_netsnow
        "integer",  # ecr_greater_netsnow
        "integer",  # delta_netgain_top30
        "integer",  # gcr_greater_netgain
        "integer",  # ecr_greater_netgain
        "integer",  # not_in_top30
        "integer",  # missing_ranks
        "integer",  # prefixes_ecr_top30
        "integer",  # prefixes_gcr_top30
        "integer",  # prefixes_gcr_total
        "numeric"   # avg_missing
        ))
}

plot_cr_error <- function() {
#### SETUP PLOT
    #par(mar=c(5,4,4,4)+0.1)
    layout(
        matrix(c(1,2), 2, 1, byrow = TRUE),
        widths=c(1),
        heights=c(2,4))
    ylims = c(
        min(-1*cidr.compare$ecr_greater_netsnow,
            -1*cidr.compare$ecr_greater_netgain),
        max(cidr.compare$gcr_greater_netsnow,
            cidr.compare$gcr_greater_netgain))
    unit_ylims = c(ylims[1] / ylims[2], 1)

#### PLOT 1
    par(mar=c(0,5,2,3))
    # PLOT data available; light grey
    plot(
        cidr.compare$date,
        rep(1,length(cidr.compare$date)),
        type="h",
        col="grey95",
        ylim=c(0,1),
        xaxt="n",
        yaxt="n",
        xlab="",
        ylab="")
    # PLOT #ASes not in top 30; dark grey
    par(new=TRUE)
    plot(
        cidr.compare$date,
        cidr.compare$not_in_top30,
        type="h",
        col="grey70",
        ylim=c(0,30),
        xaxt="n",
        xlab="",
        ylab="#ASes",
        main="Number of ASes on the Huston/Bates CIDR Report not in the top 30 of the Woodrow CIDR Report")
    mtext("", side=4, line=3, font=1)

#### PLOT 2
    par(mar=c(3,5,2,3))
    # PLOT data available; light grey
    plot(
        cidr.compare$date,
        rep(1,length(cidr.compare$date)),
        type="h",
        col="grey95",
        ylim=c(0,1),
        xaxt="n",
        yaxt="n",
        xlab="",
        ylab="")
    # PLOT delta netsnow prefixes for ASes where GCR > ECR; blue
    par(new=TRUE)
    plot(
        cidr.compare$date,
        cidr.compare$gcr_greater_netsnow,
        type='l',
        col='blue',
        ylim=ylims,
        xlab="",
        ylab=expression(paste(Sigma,"|", Delta,"prefixes|")),
        main="Comparison of Woodrow and Huston/Bates CIDR Reports")
    # PLOT delta netsnow prefixes for ASes where GCR < ECR; blue
    par(new=TRUE)
    plot(
        cidr.compare$date,
        -1*cidr.compare$ecr_greater_netsnow,
        type='l',
        col='blue',
        ylim=ylims,
        xlab="",
        ylab="",
        xaxt="n",
        yaxt="n")
    # PLOT delta netgain prefixes for ASes where GCR > ECR; red
    par(new=TRUE)
    plot(
        cidr.compare$date,
        cidr.compare$gcr_greater_netgain,
        type='l',
        col='red',
        ylim=ylims,
        xaxt="n",
        yaxt="n",
        xlab="",
        ylab="")
    # PLOT delta netgain prefixes for ASes where GCR < ECR; red
    par(new=TRUE)
    plot(
        cidr.compare$date,
        -1*cidr.compare$ecr_greater_netgain,
        type='l',
        col='red',
        ylim=ylims,
        xaxt="n",
        yaxt="n",
        xlab="",
        ylab="")


    # PLOT fraction of total netsnow contributed by top30; green
    par(new=TRUE)
    plot(
        cidr.compare$date,
        cidr.compare$prefixes_gcr_top30/cidr.compare$prefixes_gcr_total,
        type='l',
        col='green',
        ylim=unit_ylims,
        xaxt="n",
        yaxt="n",
        xlab="",
        ylab="")
    axis(4, pretty(unit_ylims,5))
#    # PLOT ratio/fraction of delta_netgain in the top30 to netsnow in the top30
#    par(new=TRUE)
#    plot(
#        cidr.compare$date,
#        cidr.compare$delta_netgain_top30/cidr.compare$prefixes_gcr_top30,
#        type='l',
#        col='red',
#        ylim=unit_ylims,
#        xaxt="n",
#        yaxt="n",
#        lty=2,
#        xlab="",
#        ylab="")
#
    legend(
        'topright',
        c(
            expression(Delta~netsnow[top30]),
            expression(Delta~netgain[top30]),
#            expression(Delta~netgain/netsnow[top30]),
            expression(netsnow[top30]/netsnow[total])
            ),
        col=c(
            "blue",
            "red",
#            "red",
            "green"
            ),
        lty=c(
            1,
            1,
#            2,
            1
            ),
        lwd=1:1,
        bg="white",
        inset=0.02)
}

pdf_cr_error <- function() {
    pdf("gcr_ecr_error.pdf", paper="usr", width=10, height=7.5)
    plot_cr_error()
    dev.off()
}

plot_cr_data_availability <- function() {
    library(RdbiPgSQL)
    conn <- dbConnect(PgSQL(), host="mitas-2.csail.mit.edu", dbname="woodrow",
        user="woodrow", password="woodrow$mitas-2@2011")

    res <- dbSendQuery(conn,
        "select date from email_cidr_reports group by date order by date;")
    ecr.dates <- dbGetResult(res)
    ecr.dates$date = as.Date(ecr.dates$date, '%m-%d-%Y')

    res <- dbSendQuery(conn,
        "select date from gen_cidr_reports group by date order by date;")
    gcr.dates <- dbGetResult(res)
    gcr.dates$date = as.Date(gcr.dates$date, '%m-%d-%Y')

    plot(x=gcr.dates$date, y=rep(-1,times=length(gcr.dates$date)), type='h', xlim=c(min(ecr.dates$date, gcr.dates$date), max(ecr.dates$date, gcr.dates$date)), col="red", ylim=c(-2,2))
    par(new=T)
    plot(x=ecr.dates$date, y=rep(1,times=length(ecr.dates$date)), type='h', xlim=c(min(ecr.dates$date, gcr.dates$date), max(ecr.dates$date, gcr.dates$date)), ylim=c(-2,2))

    dbDisconnect(conn)
}

pdf_cr_data_availability <- function() {
    pdf("data_available.pdf", paper="usr", width=10, height=7.5)
    plot_cr_data_availability()
    dev.off()
}
# look at axis.Date to adjust axis annotation
# look at ggplot2 scale_x_datetime, etc. if axis.Date doesn't work
