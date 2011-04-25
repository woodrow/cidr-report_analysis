SELECT
	gcr.date,
	gcr.origin_as,
	gcr.rank_netgain as rank,
	gcr.nets_current as netsnow,
	gcr.nets_reduced as netgain,
	tmp.weeks,
	tmp.rank_weeks,
	tmp.netgain_weeks
from gen_cidr_reports as gcr, (
	select
		origin_as,
		count(origin_as) as weeks,
		sum(30-rank_netgain) as rank_weeks,
		sum(nets_reduced) as netgain_weeks
		from gen_cidr_reports 
		where rank_netgain < 30
		and id >= 12415379
		group by origin_as
) as tmp
where tmp.origin_as = gcr.origin_as
and id >= 12415379
order by tmp.rank_weeks desc, gcr.origin_as, gcr.date;
