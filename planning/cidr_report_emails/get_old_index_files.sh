#!/bin/bash

for year in {1994..2009}
do
    for month in {1..12}
    do
        print_month=`printf %02d $month`
        wget "http://www.merit.edu/mail.archives/nanog/$year-$print_month/index.html"
    done
done