peer_counts <- read.csv("peer_counts.csv",
    colClasses=c("Date", "integer", "integer"))
pdf("peer_counts.pdf", paper="usr", width=10, height=7.5)
plot(peer_counts$date, peer_counts$median, t="h", ylim=range(peer_counts$max), ylab="routes seen by peers", xlab="date")
par(new=T)
plot(peer_counts$date, peer_counts$max, t="l", col="red", ylab="",
    main="Peer Counts")
legend("topleft", c("max. peer","median peer"), col=c("red","black"), lty=1:1, lwd=1:2);
dev.off()
