if(!exists('cidr.compare')) {
    cidr.compare = read.csv("cidr_report_validity.csv",
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
        "integer",  # min_missing_rank
        "integer",  # missing_ranks
        "integer",  # missing_delta_ranks
        "integer",  # min_missing_delta_ranks
        "integer",  # max_missing_delta_ranks
        "integer",  # delta_rank
        "integer",  # gcr_greater_rank
        "integer",  # ecr_greater_rank
        "integer",  # prefixes_ecr_top30
        "integer",  # prefixes_gcr_top30
        "integer",  # prefixes_gcr_total
        "numeric"   # avg_missing
        ))
}

cex = 0.75

xlims = c(as.Date(paste(c('19', as.POSIXlt(min(cidr.compare$date))$year, '-01-01'), collapse='')),
    as.Date(paste(c('20', (as.POSIXlt(max(cidr.compare$date))$year+1)%%100, '-01-01'), collapse='')))

plot_top30_error <- function() {
    par(cex=cex)
    par(mar=c(5,5,2,4))
    ylims=c(0,40)
    # PLOT data available; light grey
    plot(
        cidr.compare$date,
        rep(1,length(cidr.compare$date)),
        type="h",
        col="grey95",
        xlim=xlims,
        ylim=c(0,1),
        xaxt="n",
        yaxt="n",
        xlab="",
        ylab=""
    )
    par(new=TRUE)
    plot(
        cidr.compare$date,
        30-cidr.compare$min_missing_rank,
        type="l",
        col="red",
        lwd=1,
        xlim=xlims,
        ylim=ylims,
        xaxt="n",
        xlab="",
        ylab="",
        yaxt="n"
        #,log='y'
    )
    # PLOT #ASes not in top 30; dark grey
    par(new=TRUE)
    plot(
        cidr.compare$date,
        cidr.compare$not_in_top30,
        type="h",
        col="grey40",
        xlim=xlims,
        ylim=ylims,
        xaxt="n",
        xlab="Date",
        yaxt="n",
        ylab="ACR ASes not in GCR top 30",
        main=""
    )

    axis.Date(1, at=seq(min(xlims), max(xlims), "1 years"))
    count_labels = pretty(c(0,30),6)
    rank_labels = pretty(c(0,30),6)
    axis(2, count_labels, count_labels)
    axis(4, rank_labels, rev(rank_labels))
    mtext("Rank of first ACR AS not in GCR top 30", side=4, line=2, cex=cex)

    legend(
    'topright',
    c("ACR ASes not in GCR top 30", "Rank of first ACR AS not in GCR top 30"),
    col=c("grey40","red"),
    lty=c(1,1),
    lwd=1:1,
    bg="white",
    inset=0.02)
}

plot_rank_error <- function() {
    par(cex=cex)
    ylims=c(1, max(cidr.compare$min_missing_delta_ranks, cidr.compare$max_missing_delta_ranks))
    ylims=c(0,200)
    par(mar=c(5,5,2,2))
    plot(
        cidr.compare$date,
        rep(1,length(cidr.compare$date)),
        type="h",
        col="grey95",
        xlim=xlims,
        ylim=c(0,1),
        xaxt="n",
        yaxt="n",
        xlab="",
        ylab="")
    par(new=TRUE)
    plot(
        cidr.compare$date,
        cidr.compare$min_missing_delta_ranks,
        type="l",
        col="blue",
        xlim=xlims,
        ylim=ylims,
        xaxt="n",
        xlab="Date",
        ylab=expression(Delta~rank~"(for ACR ASes not in GCR top 30)")
        #,log='y'
    )
    par(new=TRUE)
    plot(
        cidr.compare$date,
        cidr.compare$max_missing_delta_ranks,
        type="l",
        col="red",
        xlim=xlims,
        ylim=ylims,
        xaxt="n",
        xlab="",
        ylab=""
        #,log='y'
    )
    axis.Date(1, at=seq(min(xlims), max(xlims), "1 years"))
    legend(
        'topright',
        c(
            expression(maximum~Delta~rank),
            expression(minimum~Delta~rank)
#            expression(Delta~netgain/netsnow[top30]),
#            expression(netsnow[top30]/netsnow[total])
            ),
        col=c(
            "red",
            "blue"
#            "red",
#            "green"
            ),
        lty=c(
            1,
            1
#            2,
#            1
            ),
        lwd=1:1,
        bg="white",
        inset=0.02)
}

plot_prefix_error <- function() {
    par(cex=cex)
    ylims = c(
        min(-1*cidr.compare$ecr_greater_netsnow,
            -1*cidr.compare$ecr_greater_netgain),
        max(cidr.compare$gcr_greater_netsnow,
            cidr.compare$gcr_greater_netgain))
    unit_ylims = c(ylims[1] / ylims[2], 1)
    #par(mar=c(3,6,2,6))
    par(mar=c(5,5,2,5))
    # PLOT data available; light grey
    plot(
        cidr.compare$date,
        rep(1,length(cidr.compare$date)),
        type="h",
        col="grey95",
        xlim=xlims,
        ylim=c(0,1),
        xaxt="n",
        yaxt="n",
        xlab="Date",
        ylab="")
    # PLOT delta netsnow prefixes for ASes where GCR > ECR; blue
    par(new=TRUE)
    plot(
        cidr.compare$date,
        cidr.compare$gcr_greater_netsnow,
        type='l',
        col='blue',
        xlim=xlims,
        ylim=ylims,
        xlab="",
        xaxt="n",
        yaxt='n',
        ylab="",
        main="")
    #mtext(expression(paste(Sigma,"(", Delta,"prefixes) where")),
    #    side=2, line=4, cex=cex)
    #mtext("GCR exceeds ACR",
    #    side=2, line=3, cex=cex)
    mtext(expression(paste(Sigma,"(", Delta,"prefixes) where GCR exceeds ACR")),
        side=2, line=3, cex=cex)
    yticks = pretty(c(0, max(ylims)), 10)
    axis(2, yticks, abs(yticks))
    #mtext(expression(paste(Sigma,"(", Delta,"prefixes) where")),
    #    side=4, line=2, cex=cex)
    #mtext("ACR exceeds GCR",
    #    side=4, line=3, cex=cex)
    mtext(expression(paste(Sigma,"(", Delta,"prefixes) where ACR exceeds GCR")),
        side=4, line=2, cex=cex)
    yticks = pretty(c(min(ylims), 0), 3)
    axis(4, yticks, abs(yticks))
    axis.Date(1, at=seq(min(xlims), max(xlims), "1 years"))
    # PLOT delta netsnow prefixes for ASes where GCR < ECR; blue
    par(new=TRUE)
    plot(
        cidr.compare$date,
        -1*cidr.compare$ecr_greater_netsnow,
        type='l',
        col='blue',
        xlim=xlims,
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
        xlim=xlims,
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
        xlim=xlims,
        ylim=ylims,
        xaxt="n",
        yaxt="n",
        xlab="",
        ylab="")

#    # PLOT fraction of total netsnow contributed by top30; green
#    par(new=TRUE)
#    plot(
#        cidr.compare$date,
#        cidr.compare$prefixes_gcr_top30/cidr.compare$prefixes_gcr_total,
#        type='l',
#        col='green',
#        xlim=xlims,
#        ylim=unit_ylims,
#        xaxt="n",
#        yaxt="n",
#        xlab="",
#        ylab="")
#    axis(4, pretty(unit_ylims,5))


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
            expression(total~observed~prefixes),
            expression(aggregable~prefixes)
#            expression(Delta~netgain/netsnow[top30]),
#            expression(netsnow[top30]/netsnow[total])
            ),
        col=c(
            "blue",
            "red"
#            "red",
#            "green"
            ),
        lty=c(
            1,
            1
#            2,
#            1
            ),
        lwd=1:1,
        bg="white",
        inset=0.02)
}

plot_cr_error <- function() {
#### SETUP PLOT
    #par(mar=c(5,4,4,4)+0.1)

#### PLOT 1
    plot_rank_error()

#### PLOT 2

}

pdf_prefix_error <- function() {
    pdf("cidr_report_validity_prefix_error.pdf", width=6.5, height=4)
    plot_prefix_error()
    dev.off()
}

pdf_rank_error <- function() {
    pdf("cidr_report_validity_rank_error.pdf", width=6.5, height=3)
    plot_rank_error()
    dev.off()
}

pdf_top30_error <- function() {
    pdf("cidr_report_validity_top30_error.pdf", width=6.5, height=3)
    plot_top30_error()
    dev.off()
}

pdf_cidr_report_validity_all <- function() {
    pdf_prefix_error()
    pdf_rank_error()
    pdf_top30_error()
}
