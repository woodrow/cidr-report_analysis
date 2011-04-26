cex = 0.75

get_cr_data <- function() {
    library(RPostgreSQL)
    conn <- dbConnect(
        PostgreSQL(),
        host="mitas-2.csail.mit.edu",
        dbname="woodrow",
        user="woodrow",
        password="woodrow$mitas-2@2011"
    )
    res = dbSendQuery(conn, paste(
        "SELECT date",
        "FROM email_cidr_reports",
        "GROUP BY date",
        "ORDER BY date;"))
    ecr.dates = fetch(res,n=-1)
    ecr.dates$date = as.Date(ecr.dates$date, '%m-%d-%Y')
    ecr.dates <<- ecr.dates

    res = dbSendQuery(conn, paste(
        "SELECT date",
        "FROM gen_cidr_reports",
        "GROUP BY date",
        "ORDER BY date;"))
    gcr.dates = fetch(res,n=-1)
    gcr.dates$date = as.Date(gcr.dates$date, '%m-%d-%Y')
    gcr.dates <<- gcr.dates

    dbDisconnect(conn)
}

plot_cr_data_availability <- function() {
#    xlims = c(
#        min(ecr.dates$date, gcr.dates$date),
#        max(ecr.dates$date, gcr.dates$date))
    xlims = c(as.Date(paste(c('19', as.POSIXlt(min(ecr.dates$date))$year, '-01-01'), collapse='')),
    as.Date(paste(c('20', (as.POSIXlt(max(ecr.dates$date))$year+1)%%100, '-01-01'), collapse='')))
    par(cex=cex)
    par(mar=c(5,3,2,2))
    plot(
        x=gcr.dates$date,
        y=rep(-1,times=length(gcr.dates$date)),
        type='h',
        xlim=xlims,
        col="darkgray",
        ylim=c(-1,1),
        ylab="",
        xlab="Date",
        yaxt='n',
        xaxt='n'
    )
    mtext("data available", cex=cex, side=2, line=1)
    mtext("GCR    ACR", cex=cex, side=2, line=0)
    axis.Date(1, at=seq(min(xlims), max(xlims), "1 years"))
    par(new=T)
    plot(
        x=ecr.dates$date,
        y=rep(1,times=length(ecr.dates$date)),
        type='h',
        xlim=xlims,
        ylim=c(-1,1),
        ylab="",
        yaxt='n',
        xaxt='n'
    )
}

pdf_cr_data_availability <- function() {
    pdf("data_avail.pdf", width=6.5, height=2)
    plot_cr_data_availability()
    dev.off()
}
