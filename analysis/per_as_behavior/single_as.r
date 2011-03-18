if(!exists('gcr')) {
    gcr <- read.csv("cidr_reported_as_data.csv",
        colClasses=c("Date", "integer", "integer", "integer", "integer", "integer",
        "integer", "integer"))
    gcr.split <- split(gcr, factor(gcr$origin_as, levels=unique(gcr$origin_as)))

    gcr.totals <- read.csv("cidr_reports_top30_totals.csv",
        colClasses=c("Date", "integer", "integer"))
}

xrange=c(min(gcr$date),max(gcr$date))

plot_as <- function(origin_as) {
    origin_as <- as.character(origin_as)
    if(origin_as %in% names(gcr.split)) {
        cr <- gcr.split[[origin_as]]

        par(mar=c(8,4,4,2)+0.1)
        plot(cr$date, (cr$rank < 30), xlab="", xaxt="n", type="h", ylim=c(0,1),
            yaxt="n", ylab="", col="lightskyblue", xlim=xrange)
        par(new=TRUE)
        plot(cr$date, (30-cr$rank)*(cr$rank < 30), xlab="", ylab="",
            type="h", ylim=c(0,30), yaxt="n", xaxt="n", col="darkgrey",
            xlim=xrange)
        par(new=TRUE)
        plot(cr$date, cr$netsnow, xlab="", ylab="prefixes", type="l",
            main=paste('AS', origin_as, sep=""),
            ylim=c(0,max(cr$netsnow, cr$netgain)), col="black", xlim=xrange)
        par(new=TRUE)
        plot(cr$date, cr$netgain, xlab="", ylab="", type="l", xaxt="n",
            yaxt="n", ylim=c(0,max(cr$netsnow, cr$netgain)), col="orange",
            xlim=xrange)
        par(new=TRUE)
        plot(cr$date, cr$netgain/cr$netsnow, xlab="", ylab="", type="l",
            xaxt="n", yaxt="n", ylim=c(0,1),
            col="red", xlim=xrange)
        par(new=TRUE)
        plot(cr$date, cr$netsnow/(gcr.totals$netsnow_top30[(gcr.totals$date %in% cr$date)]), xlab="", ylab="", xaxt="n", yaxt="n", type="l",
            ylim=c(0,1), col="darkblue", xlim=xrange)
        par(new=TRUE)
        plot(cr$date, cr$netgain/(gcr.totals$netgain_top30[(gcr.totals$date %in% cr$date)]), xlab="", ylab="", xaxt="n", yaxt="n", type="l",
            ylim=c(0,1), col="darkgreen", xlim=xrange)
        axis(4, pretty(c(0,1),10))
        #mtext("fraction", side=4, line=3, font=2)
        par(new=FALSE)
        par(xpd=TRUE)
        legend(
            'bottom',
            c("netsnow","netgain","% deagg", "% of top30 netsnow",
            "% of top30 netgain"),
            col=c("black","orange", "red", "darkblue", "darkgreen"),
            lty=1:1,
            lwd=1:1,
            bg="white",
            horiz=TRUE,
            inset=c(0,-0.2));

    } else {
        return (FALSE)
    }
}
