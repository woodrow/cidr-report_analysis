# Thesis To-Do stuff

## General Tasks
- _Outline and schedule, working back from first week of April_
- Find, download, and parse Cidr-report emails from NANOG
    - check for consistency in handoff between Tony Bates -> Geoff Huston, etc.
    - take particular note of the AS vantage point that is used for each series
      of Cidr-reports
    - start with index archives I've already collected (perhaps notes in notebook v.1)
- database schema for cidr report data
- validity-check my generated cidr report against official cidr report
- what, if anything, to do about MOASes
- Can I find ways to measure TE, etc.? (see RAS' presentation)
- Look for a measurement/etc. paper about the prevalence of operator-initiated aggregation and the presence of AS\_SETs in the AS\_PATH attribute, as well as the ATOMIC_AGGREGATE and/or AGGREGATOR attributes

## Programming
- run against the full table to determine performance and accuracy/validity numbers
    - think about the effectiveness of looking at the min of the netsaggr from each vantage point to get something close to what geoff huston has
- modify cross-table aggregation to provide optimistic and pessimistic results:
    - i.e. pessimistic: if any table can aggregate a prefix, then all tables should be able to
    - i.e. optimistic: if any table can't aggregate a prefix, there is a valid routing policy reason for not doing so
- modify straightenRV
- processing sanity checker:
    - intermediate steps:
        - capture debug/error output and raise a flag if there are too many (i.e. rejected AS_SET routes, etc.)
        - check `wc -l` of .txtrib, etc. against initial table, etc.
    - post-processing
        - compare emailed cidr report against my generated cidr report
        - compare .ppapp and .peers and highlight any major outliers
        - total netsnow, etc. and compare against raw table
- think about implementing a virtual node creation algorithm, and how to do it
    - keep statistical track of each unique as_path that passes a particular node, and announce the most?
    - this seems like an optimization problem to me if multiple as_paths pass a particular node -- how do you know whether it's better to announce that node and then the outlier sub-prefixes, or to instead announce two/three/four/etc. subnets?
    - **"SOLUTION"** for now: it would probably be easy to implement the "degenerate" case of a single as_path, but harder to generalize
- plot tree graphs of CMCST and/or TWTC and study, as MITAS/etc. has contacts with those organizations

## People to email
- Geoff Huston regarding the algorithm used by the algorithm, whether it adds/uses artificial (unannounced), less-specific "virtual prefixes", etc. as well as what he thinks about its effectiveness, people's comments and thoughts on its accuracy, etc.
    - also, ask him for the ASes that peer with as2.0
- Tony Bates, Geoff Huston, etc. regarding the report and its history
- Bruce Davie regarding the marginal cost of a router FIB slot, as compared with the growth of the routing table and the topological growth of networks (also measured by routing table?), as well as other factors raising table size concerns (IPv6 and dual stack tables, etc.)
    - think about seeing whether i can develop an index for this
    - compare against other technical evolutions/changes: MPLS, etc.
    - compare against complexity and other motivations for "legit" deaggregation
        - hijacking
        - traffic engineering
        - economies/diseconomies of scale (i.e. a small provider vs. a large provider -- how many full-table routers does each need?)
- RAS about his presentation and any other thoughts he may have
- RIPE report authors?

## Longer term writing/thinking tasks
- who's routing table(s) matter, and how representative is the CIDR report when outliers can so greatly influence the aggregation report?
- think about elaborating upon this topic in IPv6
- Justifying my case selection
    - small community
    - effective social forces
    - "ground truth" measured by third party about "bad" behavior
    - note that the CIDR report doesn't involve any new technology, organization, etc.
- things to discuss (from p. 37)
    - framing the problem of route aggregation and routing table growth more generally as one of collective action amongst ISPs
    - discussion/note of the fact that there is no centralized governance of internet operations -- the orgs that do exist mainly provide coordiation
        - ICANN, RIRs, IETF, etc. (no guarantees of routability, etc.)
    - discussion of community, norms, gatherings, and social forces within the operations community, as well as the general business/profit motives that underlie the ISP business
    - "is this really a problem?"
    - the cost and acceptability of legitimate and "non-legitimate" deaggregation and route injection
    - equity problems involved in routing table growth
        - i.e. do the costs for maintaining a full table affect small and large/well-capitalized actors differently?
- was the CIDR report effective? If so, why do/did people put stock it in? Have these considerations changed?

## "parking lot" -- things I could analyze but probably won't
- ownership of netblocks -- announcing a customer's prefix on their behalf counts against your netsnow and/or deaggregation, not the IP block owner's count (i.e. in the case of Apple, they could probably lower their agg count by a few prefixes if they installed BGP-speaking routers in some offices instead of having ATT static route them)
- the presence of explicit in-router aggregation -- looking for AS_SETs (working to deprecate, https://wiki.tools.ietf.org/html/draft-ietf-idr-deprecate-as-sets-02) or ATOMIC\_AGGREGATE attributes (also, https://wiki.tools.ietf.org/html/rfc4271#section-9.2.2 -- efficient organization of routing information)
    - **more importantly** the as_set deprecation movement shows that aggregation isn't popular, and needs to go away for RPKI
- is the notion of "prefix clusters" in (Bu, 2002) useful?

## Analytical approaches
- Chintan suggests econometrics
- control/index against various factors
    - size of community
    - decreasing price of technology

## Literature
- Bu et al
- RIPE Report on routing aggregation (mentions Cidr report & Cidr Police)
- Cittadini & Bush
- generally, IEEE transactions on networking oct/nov 2010 (or thereabouts)
- RAS' NANOG presentation -- "an inconvenient prefix"
- Greene NANOG presentation -- "CIDR Police"

## Other references
- interviews/dicussions with Martin Hannigan
- Emails from Arthur to Marty and Patrick Gilmore

## Broad classes of "solutions" to the routing table growth problem
- "shame"/social forces/non-economic incentives
- pricing of routing table slots, settlement, etc.
    - Bill Herrin's "cost of a routing table slot" document, etc.
    - pricing and capacity history of ASBR-class routers
    - difference in incentives and equity compared to interconneciton
- dictatorial control by market power and thought leadership (i.e. VZ policy on /32s)
- technical solutions
    - outside of BGP: i.e. LISP, other things from IRTF RRG etc.
    - within BGP (i.e. forgetful routing tables, in-router aggregation, route filtering, etc.)

## Interesting things in my notebook
- p. 17 -- illustration of disparity in routing tables from various RouteViews peers
- p. 18 -- discussion of different as_path comparison techniques
- p. 19 -- optimization of terrible performance
- p. 22-23 -- arthur+my routing policy equivalence algorithm, which was a false start
- p. 25 -- back of the envelope calculation about optimization, memory usage, etc.
- p. 26 -- multicore process scheduling programs
- p. 36 -- interesting /8s for visualization, etc., including the selection of 17.0.0.0/8
- p. 38-40 -- information about the routes and max. aggregation claimed for 17.0.0.0/8
- p. 44 -- description of my new approach of aggregation within the router
- p. 50 -- more optimization and debugging -- i like the "FACTS. HYPOTHESES. FACTS. ..."  pattern
- p. 51 -- realization that Geoff Huston must be adding unannounced, "virtual prefixes" in order to maximize aggregation
-