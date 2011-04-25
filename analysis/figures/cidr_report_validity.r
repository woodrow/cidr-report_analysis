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

xlims = c(as.Date(paste(c('19', as.POSIXlt(min(cidr.compare$date))$year, '-01-01'), collapse='')),
    as.Date(paste(c('20', (as.POSIXlt(max(cidr.compare$date))$year+1)%%100, '-01-01'), collapse='')))

plot_rank_error <- function() {
    par(mar=c(3,5,2,2))
    layout(
    matrix(c(1,2), 2, 1, byrow = TRUE),
    widths=c(1),
    heights=c(1,2))
    par(mar=c(0,5,2,2))
    ylims=c(1, max(cidr.compare$min_missing_delta_ranks, cidr.compare$max_missing_delta_ranks))
    ylims=c(0,200)
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
        ylab="")
    # PLOT #ASes not in top 30; dark grey
    par(new=TRUE)
    plot(
        cidr.compare$date,
        cidr.compare$not_in_top30,
        type="h",
        col="black",
        xlim=xlims,
        ylim=c(0,30),
        xaxt="n",
        xlab="",
        #yaxt="n",
        ylab="Number of ASes not in top 30",
        main="")
    par(mar=c(3,5,1,2))
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
        xlab="",
        ylab="delta_rank"
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
}

plot_prefix_error <- function() {
    ylims = c(
        min(-1*cidr.compare$ecr_greater_netsnow,
            -1*cidr.compare$ecr_greater_netgain),
        max(cidr.compare$gcr_greater_netsnow,
            cidr.compare$gcr_greater_netgain))
    unit_ylims = c(ylims[1] / ylims[2], 1)
    par(mar=c(3,6,2,6))
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
    mtext(expression(paste(Sigma,"|", Delta,"prefixes|")), side=2, line=4)
    mtext("Generated CIDR report exceeds authoritative CIDR report", side=2, line=3)
    yticks = pretty(c(0, max(ylims)), 10)
    axis(2, yticks, abs(yticks))
    mtext(expression(paste(Sigma,"|", Delta,"prefixes|")), side=4, line=2)
    mtext("Authoritative CIDR report exceeds generated CIDR report", side=4, line=3)
    yticks = pretty(c(min(ylims), 0), 5)
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
            expression(Delta~netsnow[top30]),
            expression(Delta~netgain[top30])
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
    pdf("cidr_report_validity_prefix_error.pdf", paper="usr", width=10, height=7.5)
    plot_prefix_error()
    dev.off()
}

pdf_rank_error <- function() {
    pdf("cidr_report_validity_rank_error.pdf", paper="usr", width=10, height=7.5)
    plot_rank_error()
    dev.off()
}
