import os
import datetime
import re

def extract_rib_date(rib_path):
    rib_name = os.path.basename(rib_path)
    try:
        return datetime.datetime.strptime(
            re.search('(\d{4}\-\d{2}\-\d{2})', rib_name).groups()[0],
            '%Y-%m-%d').date()
    except AttributeError:
        return datetime.datetime.strptime(
            re.search('(\d{8})', rib_name).groups()[0], '%Y%m%d').date()
