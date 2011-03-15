mail_dates <- read.csv("cidr_r_email_dates.txt",
    colClasses=c("Date"))
pdf("nanog_cidr_r_freqs.pdf", paper="usr", width=10, height=7.5)
plot(table(cut(mail_dates[[1]], "week")),
    ylab="'CIDR R' messages per week")
plot(table(cut(mail_dates[[1]], "month")),
    ylab="'CIDR R' messages per month")
dev.off()
