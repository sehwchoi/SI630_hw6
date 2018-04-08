#! /usr/bin/env python
# -*- coding: utf-8
'''
Python implementation of Krippendorff's alpha -- inter-rater reliability

(c)2011-17 Thomas Grill (http://grrrr.org)

Python version >= 2.4 required
'''


from __future__ import print_function
import pandas as pd
import numpy as np

try:
    import numpy as np
except ImportError:
    np = None


def nominal_metric(a, b):
    return a != b


def interval_metric(a, b):
    return (a-b)**2


def ratio_metric(a, b):
    return ((a-b)/(a+b))**2


def krippendorff_alpha(data, metric=interval_metric, force_vecmath=False, convert_items=float, missing_items=None):
    '''
    Calculate Krippendorff's alpha (inter-rater reliability):
    
    data is in the format
    [
        {unit1:value, unit2:value, ...},  # coder 1
        {unit1:value, unit3:value, ...},   # coder 2
        ...                            # more coders
    ]
    or 
    it is a sequence of (masked) sequences (list, numpy.array, numpy.ma.array, e.g.) with rows corresponding to coders and columns to items
    
    metric: function calculating the pairwise distance
    force_vecmath: force vector math for custom metrics (numpy required)
    convert_items: function for the type conversion of items (default: float)
    missing_items: indicator for missing items (default: None)
    '''
    
    # number of coders
    m = len(data)
    
    # set of constants identifying missing values
    if missing_items is None:
        maskitems = []
    else:
        maskitems = list(missing_items)
    if np is not None:
        maskitems.append(np.ma.masked_singleton)
    
    # convert input data to a dict of items
    units = {}
    for d in data:
        try:
            # try if d behaves as a dict
            diter = d.items()
        except AttributeError:
            # sequence assumed for d
            diter = enumerate(d)
            
        for it, g in diter:
            if g not in maskitems:
                try:
                    its = units[it]
                except KeyError:
                    its = []
                    units[it] = its
                its.append(convert_items(g))


    units = dict((it, d) for it, d in units.items() if len(d) > 1)  # units with pairable values
    n = sum(len(pv) for pv in units.values())  # number of pairable values
    
    if n == 0:
        raise ValueError("No items to compare.")
    
    np_metric = (np is not None) and ((metric in (interval_metric, nominal_metric, ratio_metric)) or force_vecmath)
    
    Do = 0.
    for grades in units.values():
        if np_metric:
            gr = np.asarray(grades)
            Du = sum(np.sum(metric(gr, gri)) for gri in gr)
        else:
            Du = sum(metric(gi, gj) for gi in grades for gj in grades)
        Do += Du/float(len(grades)-1)
    Do /= float(n)

    if Do == 0:
        return 1.

    De = 0.
    for g1 in units.values():
        if np_metric:
            d1 = np.asarray(g1)
            for g2 in units.values():
                De += sum(np.sum(metric(d1, gj)) for gj in g2)
        else:
            for g2 in units.values():
                De += sum(metric(gi, gj) for gi in g1 for gj in g2)
    De /= float(n*(n-1))

    return 1.-Do/De if (Do and De) else 1.


if __name__ == '__main__':

    missing = '*' # indicator for missing values

    print("Krippendorff's_Alpha for civility within group")

    group_files = ["group-13-sh.tsv", "group-13-hj.tsv"]
    group_array = []
    for file in group_files:

        group_df = pd.read_csv(file, sep='\t')
        group_df_rate = list(group_df['Rate'])
        group_array.append(group_df_rate)

    print(group_array)
    print("nominal metric: %.3f" % krippendorff_alpha(group_array, nominal_metric, missing_items=missing))
    print("interval metric: %.3f" % krippendorff_alpha(group_array, interval_metric, missing_items=missing))


    print("Krippendorff's_Alpha for civility across workers")
    crdsrc = pd.read_csv('f1255407.csv')
    crdsrc = crdsrc[crdsrc['_golden'] == False]  # remove test questions
    collist = ['_worker_id', '_unit_id', 'civility']
    tbl = crdsrc[collist]
    pvt_tbl = tbl.pivot(index='_worker_id', columns='_unit_id', values='civility')

    print('Number of crowd workers:{}, Number of annoations per worker: {}'.format(pvt_tbl.shape[0], pvt_tbl.shape[1]))
    pvt_tbl = pvt_tbl.fillna(missing)

    print(pvt_tbl)
    print(type(pvt_tbl))

    #worker_rate_group_by_unit = tbl.groupby('_unit_id')['civility'].apply(list).reset_index(name='Rates')

    print(pvt_tbl.values)

    print("nominal metric: %.3f" % krippendorff_alpha(pvt_tbl.values, nominal_metric, missing_items=missing))
    print("interval metric: %.3f" % krippendorff_alpha(pvt_tbl.values, interval_metric, missing_items=missing))

