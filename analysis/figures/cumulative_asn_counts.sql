select 
acr.asn_count as acr_count, 
acr.on_or_before_date as acr_date, 
gcr.asn_count as gcr_count, 
gcr.on_or_before_date as gcr_date 
from get_cumulative_ecr_asns() as acr 
full outer join cumulative_gcr_as_counts as gcr on acr.on_or_before_date = gcr.on_or_before_date;