data_sets = c("as_rank_freq", "as_rank_durations")
for(e in data_sets) {
    if(!exists(e)) {
        library(RdbiPgSQL)
        conn <- dbConnect(
            PgSQL(),
            host="mitas-2.csail.mit.edu",
            dbname="woodrow",
            user="woodrow",
            password="woodrow$mitas-2@2011"
        )
        ########################################################################
        res = dbSendQuery(conn, paste(
            "SELECT tmp.rank, COUNT(tmp.as_count) from (",
            "    SELECT rank, COUNT(origin_as) as as_count",
            "    FROM email_cidr_reports",
            "    GROUP BY rank, origin_as",
            "    ORDER BY rank) as tmp",
            "WHERE tmp.rank < 30",
            "GROUP BY tmp.rank",
            "ORDER BY tmp.rank;"))
        as_rank_freq = dbGetResult(res)

        res = dbSendQuery(conn, paste(
            "SELECT rank, COUNT(origin_as) as as_count",
            "FROM email_cidr_reports",
            "WHERE rank < 30",
            "GROUP BY rank, origin_as",
            "ORDER BY rank;"))
        as_rank_durations = dbGetResult(res)
        ########################################################################
        dbDisconnect(conn)
        break
    }
}

plot.cr.cdfs <- function() {
    x11()
    plot(
        as_rank_freq$rank+1,
        as_rank_freq$count,
        type='h',
        ylim=c(0,max(as_rank_freq$count))
    )

    ard.split = split(as_rank_durations,
                    factor(as_rank_durations$rank, levels=unique(as_rank_durations$rank)))

    x11()
    par(mfrow=c(2,2))
    xlims = c(0,max(as_rank_durations[['as_count']]))
    colors = rainbow(8)
    for(i in c(0:29)) {
        if (i %% 8 != 0)
            par(new=T)
        plot.ecdf(
            ard.split[[as.character(i)]][['as_count']],
            xlim=xlims,
            col=colors[(i %% 8) + 1]
        )
    }

    x11()
    colors = rainbow(30)
    for(i in c(0:29)) {
        plot.ecdf(
            ard.split[[as.character(i)]][['as_count']],
            xlim=xlims,
            col=colors[i+1],
            pch=NA,
            verticals=TRUE
        )
        par(new=T)
    }
}
