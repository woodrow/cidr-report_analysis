CREATE OR REPLACE FUNCTION fliprank_gcr() RETURNS void AS $$
DECLARE
    week_date date;
    week_rank integer;
    row_cursor CURSOR (week date) FOR SELECT * FROM gen_cidr_reports
        WHERE date = week FOR UPDATE;
    row_record record;
    progress integer;
    total_weeks integer;
BEGIN
    progress := 0;
    SELECT count(*) INTO STRICT total_weeks
        FROM (SELECT date FROM gen_cidr_reports group by date) as dates;
    FOR week_date IN SELECT date FROM gen_cidr_reports GROUP BY date LOOP
        RAISE NOTICE 'starting week %', week_date;
        SELECT max(rank_netgain) INTO STRICT week_rank
            FROM gen_cidr_reports WHERE date = week_date;
        FOR row_record IN row_cursor (week_date) LOOP
            UPDATE gen_cidr_reports
            SET rank_netgain = week_rank - rank_netgain,
                rank_netsnow = week_rank - rank_netsnow
            WHERE CURRENT OF row_cursor;
        END LOOP;
        progress := progress + 1;
        RAISE NOTICE 'progress: %',
            CAST(progress as float)/CAST(total_weeks as float);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fliprank_ecr() RETURNS void AS $$
DECLARE
    week_date date;
    week_rank integer;
    row_cursor CURSOR (week date) FOR SELECT * FROM email_cidr_reports
        WHERE date = week FOR UPDATE;
    row_record record;
    progress integer;
    total_weeks integer;
BEGIN
    progress := 0;
    SELECT count(*) INTO STRICT total_weeks
        FROM (SELECT date FROM email_cidr_reports group by date) as dates;

    FOR week_date IN SELECT date FROM email_cidr_reports GROUP BY date LOOP
        RAISE NOTICE 'starting week %', week_date;
        SELECT max(rank) INTO STRICT week_rank
            FROM email_cidr_reports WHERE date = week_date;
        FOR row_record IN row_cursor (week_date) LOOP
            UPDATE email_cidr_reports
            SET rank = week_rank - rank
            WHERE CURRENT OF row_cursor;
        END LOOP;

        progress := progress + 1;
        RAISE NOTICE 'progress: %',
            CAST(progress as float)/CAST(total_weeks as float);
    END LOOP;
END;
$$ LANGUAGE plpgsql;
