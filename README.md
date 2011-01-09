cidr-report_analysis
====================

This is ongoing work related to my graduate thesis about the analysis of the
effectiveness of the CIDR Report.

Repo Layout
-----------

    Tree                    Description
    ----                    -----------
    /
    |-- cidr_analysis       Python package implementing the CIDR-Report
    |                       aggregation algorithm as well as other glue involved
    |                       in conducting my analysis (i.e. normalizing routing
    |                       tables, etc.)
    |-- libbgpdump          Modifications to RIPE's libbgpdump
    |-- planning            Planning, task lists, etc.
    |   `-- routeviews      Docs and planning for Routeviews data
    `-- rv2atoms-0.5        Modifcations to CAIDA's straightenRV

License
-------

The software located in /cidr_analysis will be relicensed under a well-known
license in the future, at which time this license notice will be changed to
reflect the new license. Until this software is relicensed, the author reserves
all copyrights.

The software in /libbgpdump and /rv2atoms are copyrighted by their respective
authors and licensed in accordance with the included license, readme, or source files.
