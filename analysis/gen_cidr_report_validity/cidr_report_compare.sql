SELECT
    cmp.*,
    tp.prefixes_gcr_total,
    cmp.missing_ranks/cmp.not_in_top30 as avg_missing
FROM (
    SELECT
        gcr.date,
        (gcr.date - '1997-11-14')/7 as week,
        sum(abs(gcr.nets_current - ecr.netsnow)) as delta_netsnow_top30,
        sum(abs(gcr.nets_reduced - ecr.netgain)) as delta_netgain_top30,
        sum(case when gcr.rank_netgain >= 30 then 1 else 0 end)
            as not_in_top30,
        sum(case when gcr.rank_netgain >= 30 then ecr.rank else 0 end)
            as missing_ranks,
        sum(ecr.netsnow) as prefixes_ecr_top30,
        sum(gcr.nets_current) as prefixes_gcr_top30
    FROM
        gen_cidr_reports as gcr,
        email_cidr_reports as ecr
    WHERE
        gcr.date = ecr.date
        AND gcr.origin_as = ecr.origin_as
    GROUP BY gcr.date
    ORDER BY gcr.date
) AS cmp, (
    SELECT
        gcr.date,
        sum(gcr.nets_current) as prefixes_gcr_total
    FROM
        gen_cidr_reports as gcr
    GROUP BY gcr.date
) AS tp
WHERE
    tp.date = cmp.date;