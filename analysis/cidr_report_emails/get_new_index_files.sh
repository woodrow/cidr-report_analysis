#!/bin/bash

cd new_indexes

for year in {2009..2010}
do
    for month in {1..12}
    do
        print_month=`printf %02d $month`
        print_date=`date -j -f %Y-%m-%d $year-$month-01 +%Y-%B`
        if [ ! -e "$year$print_month.txt.gz" ] 
            then
                wget -O "$year$print_month.txt.gz" "http://mailman.nanog.org/pipermail/nanog/$print_date.txt.gz"
        fi

#        if [ -e "$print_date.txt" ]
#            then
#                mv "$print_date.txt" "$year$print_month.txt"
#        fi
    done
done