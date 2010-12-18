# this assumes cidrprefix_treeonly has already been run, and the
# resulting data structures are in the interpreter's memory

import json

pal = [(str(x), int(str(x).split('.')[0]), x.aggregable_more_specifics,
    x.origin_as) for x in prefix_agg_list]

pal_asdict = {}
for p in pal:
    pal_asdict.setdefault(p[3],{}).setdefault(p[1],[]).append(p)

candidate_list = []
for asn in pal_asdict:
    if len(pal_asdict[asn]) == 1:
        candidate_list.append(pal_asdict[asn])
candidate_list.sort(key=lambda x: len(x.values()[0]), reverse=True)

freq_dict = {}
for l in candidate_list:
    (pfx_count, as_count) = freq_dict.get(l.keys()[0],(0,0))
    pfx_count += len(l.values()[0])
    as_count += 1
    freq_dict[l.keys()[0]] = (pfx_count,as_count)

freq_ratios = []
for k in freq_dict:
    freq_ratios.append((k, float(freq_dict[k][0])/float(freq_dict[k][1])))
freq_ratios.sort(key=lambda x: x[1], reverse=True)

interest_pfx = [122, 13, 218, 17]
interest_dict = {}
for l in candidate_list:
    pfx = l.keys()[0]
    if pfx in interest_pfx:
        interest_dict[pfx] = interest_dict.get(pfx,[]) + l.values()[0]

f = open('../nov12/classa_agg_candidates.json', 'w')
json.dump(interest_dict, f)
f.close()
