# cidr-report_analysis

This is ongoing work related to my graduate thesis about the analysis of the
effectiveness of the CIDR Report.

## Repo Layout

    Tree                    Description
    ----                    -----------
    /
    |-- analysis            R and Python files to analyze data and produce figures
    |-- cidr_analysis       Python package implementing the CIDR-Report
    |                       aggregation algorithm as well as other glue involved
    |                       in conducting my analysis (i.e. normalizing routing
    |                       tables, etc.)
    |-- libbgpdump          Modifications to RIPE's libbgpdump
    |-- planning            Planning, task lists, etc.
    |   `-- routeviews      Docs and planning for Routeviews data
    `-- rv2atoms-0.5        Modifcations to CAIDA's straightenRV

## License

### contents of `/libbgpdump` and `/rv2atoms` directories

The software in `/libbgpdump` and `/rv2atoms` are copyrighted by their respective
authors and licensed in accordance with the included license, README, or source files.

### contents of `/cidr_analysis` and other directories

The software located in `/cidr_analysis` and the other directories not already identified are licensed under the following license (the "MIT License"):

Copyright (c) 2010-2011 Stephen Woodrow

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.