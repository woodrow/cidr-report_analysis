SELECT
	gcr.date,
	sum(gcr.nets_current) as netsnow_top30,
	sum(gcr.nets_reduced) as netgain_top30
from gen_cidr_reports as gcr
where gcr.rank_netgain < 30
group by gcr.date
order by gcr.date;