asn_counts = read.csv("cumulative_asn_counts.csv",
    colClasses=c("integer", "character", "integer", "character"))
asn_counts$acr_date[asn_counts$acr_date == ""] = NA
asn_counts$acr_date = as.Date(asn_counts$acr_date)
asn_counts$gcr_date[asn_counts$gcr_date == ""] = NA
asn_counts$gcr_date = as.Date(asn_counts$gcr_date)

cex = 0.75

plot_cumulative_counts <- function() {
    xlims = c(
        min(asn_counts$acr_date[!is.na(asn_counts$acr_date)],
            asn_counts$gcr_date[!is.na(asn_counts$gcr_date)]),
        max(asn_counts$acr_date[!is.na(asn_counts$acr_date)],
            asn_counts$gcr_date[!is.na(asn_counts$gcr_date)])
        )
    xlims = c(
        as.Date(paste(c('19',
            as.POSIXlt(min(xlims))$year, '-01-01'), collapse='')),
        as.Date(paste(c('20',
            (as.POSIXlt(max(xlims))$year+1)%%100, '-01-01'), collapse=''))
        )
    ylims = c(
        min(asn_counts$acr_count[!is.na(asn_counts$acr_count)],
            asn_counts$gcr_count[!is.na(asn_counts$gcr_count)]),
        max(asn_counts$acr_count[!is.na(asn_counts$acr_count)],
            asn_counts$gcr_count[!is.na(asn_counts$gcr_count)])
        )

    layout(
        matrix(c(1,2), 2, 1, byrow = TRUE),
        widths=c(1),
        heights=c(1,1))
    par(mar=c(4,5,2,2))
    par(cex=cex)
    plot(
        x=asn_counts$acr_date[!is.na(asn_counts$acr_date)],
        y=asn_counts$acr_count[!is.na(asn_counts$acr_count)],
        type='l',
        xlim=xlims,
        #ylim=ylims,
        col='red'
        ,xaxt='n'
        ,xlab=""
        ,ylab="Cumulative number of unique ASes on ACR"
    )
    axis.Date(1, at=seq(min(xlims), max(xlims), "1 years"))
    par(mar=c(5,5,0,2))
    par(cex=cex)
    plot(
        x=asn_counts$gcr_date[!is.na(asn_counts$gcr_date)]
        ,y=asn_counts$gcr_count[!is.na(asn_counts$gcr_count)]
        ,type='l'
        ,xlim=xlims
        ,ylim=ylims
        ,col='black'
        #,log='y'
        ,xaxt='n'
        ,xlab=""
        ,ylab=""
    )
    par(new=T)
    plot(
        x=asn_counts$acr_date[!is.na(asn_counts$acr_date)]
        ,y=asn_counts$acr_count[!is.na(asn_counts$acr_count)]
        ,type='l'
        ,xlim=xlims
        ,ylim=ylims
        ,col='red'
        #,log='y'
        ,xaxt='n'
        ,yaxt='n'
        ,xlab="Date"
        ,ylab=""
    )
    axis.Date(1, at=seq(min(xlims), max(xlims), "1 years"))

    mtext("Number of ASes", side=2, line=3, cex=cex)

    legend(
    'topleft',
    c("Number of ASes visible in routing table",
        "Cumulative number of unique ASes on ACR (same as above)"),
    col=c("black","red"),
    lty=c(1,1),
    lwd=1:1,
    bg="white",
    inset=0.02)
}

pdf_cumulative_counts <- function() {
    pdf("cumulative_asn_counts.pdf", width=6.5, height=6)
    plot_cumulative_counts()
    dev.off()
}
