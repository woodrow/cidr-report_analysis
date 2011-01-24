#!/usr/bin/env python2.6

"""The enumerate object for classifying prefixes based on the methodology given 
in [1].

[1] Luca Cittadini, Wolfgang Muhlbauer, Steve Uhlig, Randy Bush, Pierre
Francois, and Olaf Maennel. 2010. Evolution of internet address space
deaggregation: myths and reality. IEEE J.Sel. A. Commun. 28, 8 (October 2010),
1238-1249. DOI=10.1109/JSAC.2010.101002 
http://dx.doi.org/10.1109/JSAC.2010.101002

"""

from enumerator import Enumerate

PREFIX_CLASSES = Enumerate('LONELY', 'TOP', 'DEAGG', 'DELEG')
