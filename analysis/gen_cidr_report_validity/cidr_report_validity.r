if(!exists('cidr.compare')) {
    cidr.compare <- read.csv("cidr_report_compare.csv",
        colClasses=c("Date", "integer", "integer", "integer", "integer",
        "integer", "integer", "integer", "integer", "numeric"))
}

plot_cr_error <- function() {
    ylims=c(
        min(cidr.compare$delta_netsnow_top30, cidr.compare$delta_netgain_top30),
        max(cidr.compare$delta_netsnow_top30, cidr.compare$delta_netgain_top30))
    par(mar=c(5,4,4,4)+0.1)
    plot(cidr.compare$date,
        rep(1,length(cidr.compare$date)), type="h", col="grey95",
        ylim=c(0,1), xaxt="n", yaxt="n", xlab="", ylab="")
    par(new=TRUE)
    plot(cidr.compare$date,
        cidr.compare$not_in_top30, type="h", col="grey70", ylim=c(0,30),
        xaxt="n", yaxt="n", xlab="", ylab="")
    axis(4, pretty(c(0,30),10))
    mtext("ASes not in top 30", side=4, line=3, font=1)
    par(new=TRUE)
    plot(cidr.compare$date, cidr.compare$delta_netsnow_top30, type='l',
        col='blue', ylim=ylims, xlab="",
        ylab=expression(paste(Sigma,"|", Delta,"prefixes|")),
        main="Comparison of Generated and Emailed CIDR Reports")
    par(new=TRUE)
    plot(cidr.compare$date, cidr.compare$delta_netgain_top30, type='l',
        col='red', ylim=ylims, xaxt="n", yaxt="n", xlab="", ylab="")
    par(new=TRUE)
    plot(cidr.compare$date,
        cidr.compare$delta_netgain_top30/cidr.compare$prefixes_gcr_top30,
        type='l', col='red', ylim=c(0,1), xaxt="n", yaxt="n", lty=2,
        xlab="", ylab="")
    legend(
        'topright',
        c(expression(Delta~netsnow[top30]),
        expression(Delta~netgain[top30]),
        expression(Delta~netgain/netsnow[top30])),
        col=c("blue","red", "red"),
        lty=c(1, 1, 2),
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
