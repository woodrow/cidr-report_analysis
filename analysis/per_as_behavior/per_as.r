library("zoo")
gcr <- read.csv("cidr_reported_as_data.csv",
    colClasses=c("Date", "integer", "integer", "integer", "integer", "integer",
    "integer", "integer"))
gcr.split <- split(gcr, factor(gcr$origin_as, levels=unique(gcr$origin_as)))

gcr.totals <- read.csv("cidr_reports_top30_totals.csv",
    colClasses=c("Date", "integer", "integer"))

pdf("per_as_plots.pdf", paper="USr", width=10, height=7.5)
par(mfrow=c(20,1), mar=c(0,4,0,0))

xrange=c(min(gcr$date),max(gcr$date))

for (origin_as in names(gcr.split)) {
    cr <- gcr.split[[origin_as]]
    plot(cr$date, (cr$rank < 30), xlab="", xaxt="n", type="h", ylim=c(0,1),
        yaxt="n", ylab="", col="lightskyblue", xlim=xrange)
    par(new=TRUE)
    plot(cr$date, (30-cr$rank)*(cr$rank < 30), xlab="", ylab=origin_as, type="h",
        ylim=c(0,30), yaxt="n", col="darkgrey", xlim=xrange)
    par(new=TRUE)
    if(length(cr$date) >= 4) {
        plot(cr$date[3:(length(cr$date)-1)],
            rollapply(zoo(cr$netgain/cr$netsnow), 4, (mean)), xlab="", ylab="",
            yaxt="n", xaxt="n",   type="l", ylim=c(0,1), xlim=xrange, col="red",
            lwd=2)
        par(new=TRUE)
        plot(cr$date[3:(length(cr$date)-1)],
            rollapply(zoo(cr$netgain/(gcr.totals$netgain_top30[(gcr.totals$date %in% cr$date)])), 4, (mean)),
            xlab="", ylab="", yaxt="n", xaxt="n",  type="l", ylim=c(0,1),
            col="blue", lwd=2)
        par(new=TRUE)
        plot(cr$date[3:(length(cr$date)-1)],
            rollapply(zoo(cr$netsnow/(gcr.totals$netsnow_top30[(gcr.totals$date %in% cr$date)])), 4, (mean)), xlab="", ylab="", yaxt="n", xaxt="n",  type="l", ylim=c(0,1), col="green", lwd=2)
    }
    par(new=FALSE)
}
