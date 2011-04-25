if(!exists('gcr')) {
    gcr <- read.csv("single_as_gcr_cr_data.csv",
        colClasses=c("Date", "integer", "integer", "integer", "integer", "integer",
        "integer", "integer"))
    gcr.split <- split(gcr, factor(gcr$origin_as, levels=unique(gcr$origin_as)))

    gcr.totals <- read.csv("single_as_gcr_totals.csv",
        colClasses=c("Date", "integer", "integer"))
}

#xrange=c(min(gcr$date),max(gcr$date))
xrange = c(as.Date('2005-01-01'),as.Date('2009-01-01'))

plot_as <- function(origin_as) {
    origin_as <- as.character(origin_as)
    if(origin_as %in% names(gcr.split)) {
        cr <- gcr.split[[origin_as]]

        par(mar=c(5,4,2,4)+0.1)
        #plot(cr$date, (cr$rank < 30), xlab="", xaxt="n", type="h", ylim=c(0,1),
        #    yaxt="n", ylab="", col="lightskyblue", xlim=xrange)
        #par(new=TRUE)
        plot(cr$date, (30-cr$rank)*(cr$rank < 30), xlab="Date", ylab="Aggregable Prefixes",
            type="h", ylim=c(0,30), yaxt="n", xaxt="n", col="darkgrey",
            xlim=xrange) #main=paste('AS', origin_as, sep=" ")
        axis.Date(1, at=seq(min(xrange), max(xrange), "1 year"))
        plot_labels = pretty(c(1,30),6)
        axis(4, plot_labels, rev(plot_labels))
        mtext("CIDR Report Rank", side=4, line=2)
        par(new=TRUE)
        #plot(cr$date, cr$netsnow, xlab="", ylab="", type="l",
        #    ylim=c(0,max(cr$netsnow, cr$netgain)), col="black", xlim=xrange)
        #par(new=TRUE)
        plot(
            cr$date,
            cr$netgain,
            xlab="",
            ylab="",
            type="l",
            xaxt="n",
            ylim=c(0,max(cr$netsnow, cr$netgain)),
            col="black",
            xlim=xrange)
#        par(new=TRUE)
#        plot(cr$date, cr$netgain/cr$netsnow, xlab="", ylab="", type="l",
#            xaxt="n", yaxt="n", ylim=c(0,1),
#            col="red", xlim=xrange)
#        par(new=TRUE)
#        plot(cr$date, cr$netsnow/(gcr.totals$netsnow_top30[(gcr.totals$date %in% cr$date)]), xlab="", ylab="", xaxt="n", yaxt="n", type="l",
#            ylim=c(0,1), col="darkblue", xlim=xrange)
#        par(new=TRUE)
#        plot(cr$date, cr$netgain/(gcr.totals$netgain_top30[(gcr.totals$date %in% cr$date)]), xlab="", ylab="", xaxt="n", yaxt="n", type="l",
#            ylim=c(0,1), col="darkgreen", xlim=xrange)
#        par(new=FALSE)
            par(xpd=TRUE)
#        legend(
#            'bottom',
#            c("netsnow","netgain","% deagg", "% of top30 netsnow",
#            "% of top30 netgain"),
#            col=c("black","orange", "red", "darkblue", "darkgreen"),
#            lty=1:1,
#            lwd=1:1,
#            bg="white",
#            horiz=TRUE,
#            inset=c(0,-0.2));
#
    } else {
        return (FALSE)
    }
}

pdf_plot_measurment_example <- function() {
    pdf("single_as.pdf", paper="us", width=6.5, height=4)
    plot_as(3602)
    dev.off()
}
