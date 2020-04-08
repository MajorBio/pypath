#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  This file is part of the `pypath` python module
#
#  Copyright
#  2014-2020
#  EMBL, EMBL-EBI, Uniklinik RWTH Aachen, Heidelberg University
#
#  File author(s): Dénes Türei (turei.denes@gmail.com)
#                  Nicolàs Palacio
#                  Olga Ivanova
#
#  Distributed under the GPLv3 License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  Website: http://pypath.omnipathdb.org/
#

"""
Interface to UniProt protein datasheets.
"""

from future.utils import iteritems

import os
import sys
import re
import importlib as imp
import collections
import itertools

import pypath.inputs.uniprot as uniprot_input
import pypath.share.common as common


class UniprotProtein(object):
    
    _relength = re.compile(r'([0-9]+) AA')
    _rename = re.compile(r'Name=(\w+);')
    _rerecname = re.compile(r'RecName: Full=([^;]+);')
    _recc = re.compile(r'-!- ([A-Z ]+):\s?(.*)')
    _remw = re.compile(r'([0-9]+) MW')
    _redb = re.compile(r'([^;]+);\s?(.*)\s?\.\s?(?:\[(.*)\])?')
    _redbsep = re.compile(r'\s?;\s?')
    
    def __init__(self, uniprot_id):
        
        self.uniprot_id = uniprot_id
        self.load()
    
    
    def reload(self):

        modname = self.__class__.__module__
        mod = __import__(modname, fromlist = [modname.split('.')[0]])
        imp.reload(mod)
        new = getattr(mod, self.__class__.__name__)
        setattr(self, '__class__', new)
    
    
    def load(self):
        
        self.raw = uniprot_input.protein_datasheet(self.uniprot_id)
    
    
    @property
    def is_reviewed(self):
        
        return 'Reviewed' in self.raw[0][1]
    
    
    @property
    def id(self):
        
        return self.raw[0][1].split()[0]
    
    
    @property
    def ac(self):
        
        return next(self.itertag('AC')).split(';')[0]
    
    
    @property
    def length(self):
        """
        Returns the length (number of residues) of the canonical sequence.
        """
        
        return int(self._relength.search(self.raw[0][1]).groups()[0])
    
    
    @property
    def organism(self):
        
        return int(next(self.itertag('OX')).split('=')[1][:-1])
    
    
    @property
    def full_name(self):
        
        return self._rerecname.search(next(self.itertag('DE'))).groups()[0]
    
    
    @property
    def info(self):
        
        if not hasattr(self, '_info'):
            
            self.update_info()
        
        return self._info
    
    
    def update_info(self):
        
        result = collections.defaultdict(list)
        title = None
        
        for cc in self.itertag('CC'):
            
            if cc.startswith('---'):
                
                break
            
            m = self._recc.match(cc)
            
            if m:
                
                title, cc = m.groups()
            
            line = cc.strip()
            
            if line:
                
                result[title].append(line)
        
        self._info = dict(
            (
                title,
                ' '.join(line)
            )
            for title, line in iteritems(result)
        )
    
    
    @property
    def function(self):
        
        return self.info_section('FUNCTION')
    
    
    @property
    def subcellular_location(self):
        
        return self.info_section('SUBCELLULAR LOCATION')
    
    
    @property
    def tissue_specificity(self):
        
        return self.info_section('TISSUE SPECIFICITY')
    
    
    @property
    def subunit(self):
        
        return self.info_section('SUBUNIT')
    
    
    @property
    def interaction(self):
        
        return self.info_section('INTERACTION')
    
    
    @property
    def sequence_caution(self):
        
        return self.info_section('SEQUENCE CAUTION')
    
    
    @property
    def catalytic_activity(self):
        
        return self.info_section('CATALYTIC ACTIVITY')
    
    
    @property
    def activity_regulation(self):
        
        return self.info_section('ACTIVITY REGULATION')
    
    
    @property
    def alternative_products(self):
        
        return self.info_section('ALTERNATIVE PRODUCTS')
    
    
    @property
    def ptm(self):
        
        return self.info_section('PTM')
    
    
    @property
    def disease(self):
        
        return self.info_section('DISEASE')
    
    
    @property
    def similarity(self):
        
        return self.info_section('SIMILARITY')
    
    
    @property
    def web_resource(self):
        
        return self.info_section('WEB RESOURCE')
    
    
    @property
    def lengths(self):
        """
        Returns the length of all isoforms as a list.
        """
        
        return [
            int(self._relength.search(sq).groups()[0])
            for sq in self.itertag('SQ')
        ]
    
    
    @property
    def weight(self):
        """
        Returns the molecular weight of the canonical isoform in Daltons.
        """
        
        return int(self._remw.search(next(self.itertag('SQ'))).groups()[0])
    
    
    @property
    def weights(self):
        """
        Returns the molecular weights of all isoforms as a list.
        """
        
        return [
            int(self._remw.search(sq).groups()[0])
            for sq in self.itertag('SQ')
        ]
    
    
    @property
    def databases(self):
        """
        Returns the database identifiers (cross-references) as a dict of
        database names and identifiers.
        """
        
        if not hasattr(self, '_databases'):
            
            self.update_databases()
        
        return self._databases
    
    
    def update_databases(self):
        
        result = collections.defaultdict(set)
        
        for db in self.itertag('DR'):
            
            m = self._redb.match(db)
            
            if m:
                
                dbname, ids, subtype = m.groups()
                ids = self._redbsep.split(ids)
                ids = tuple(_id for _id in ids if _id != '-')
                
                if subtype:
                    
                    ids += (subtype,)
                
                ids = ids[0] if len(ids) == 1 else ids
                result[dbname].add(ids)
        
        self._databases = dict(result)
    
    
    def info_section(self, title):
        """
        Retrieves a section from the description. If the section is not
        availeble, returns ``None``.
        """
        
        info = self.info
        
        if title in info:
            
            return info[title]
    
    @property
    def genesymbol(self):
        
        return self._rename.search(next(self.itertag('GN'))).groups()[0]
    
    
    @property
    def keywords(self):
        """
        Returns the keywords as a list.
        """
        
        return list(
            itertools.chain(
                *(
                    self._redbsep.split(kw.strip('.'))
                    for kw in self.itertag('KW')
                )
            )
        )
    
    
    @property
    def sequence(self):
        """
        Returns the canonical sequence (the first one) as a string of
        standard capital letter residue symbols.
        """
        
        result = []
        collect = False
        
        for tag, line in self:
            
            if not collect and tag == 'SQ':
                
                collect = True
                
            elif collect:
                
                if tag == '  ':
                    
                    result.append(line)
                    
                else:
                    
                    break
        
        return ''.join(x.replace(' ', '') for x in result)
    
    
    def __iter__(self):
        
        return self.raw.__iter__()
    
    
    def itertag(self, tag):
        
        for _tag, line in self:
            
            if _tag == tag:
                
                yield line
    
    
    def __repr__(self):
        
        return '<UniProt datasheet %s (%s)>' % (self.ac, self.genesymbol)


def _update_methods():
    
    for method_name in UniprotProtein.__dict__.keys():
        
        if method_name.startswith('_'):
            
            continue
        
        def create_method(method_name):
            
            def method(uniprot_id, *args, **kwargs):
                
                bound_m = getattr(UniprotProtein(uniprot_id), method_name)
                
                if isinstance(getattr(UniprotProtein, method_name), property):
                    
                    return bound_m
                    
                else:
                    
                    return bound_m(*args, **kwargs)
            
            return method
        
        _method = create_method(method_name)
        
        common._add_method(
            cls = sys.modules[__name__],
            method_name = method_name,
            method = _method,
            doc = getattr(UniprotProtein, method_name).__doc__,
        )


_update_methods()


def query(*uniprot_ids):
    """
    Queries the datasheet of one or more UniProt IDs.
    Returns a single ``UniprotProtein`` object or a list of those objects.
    """
    
    if (
        len(uniprot_ids) == 1 and
        isinstance(uniprot_ids, common.list_like)
    ):
        
        uniprot_ids = uniprot_ids[0]
    
    result = [
        UniprotProtein(uniprot_id)
        for uniprot_id in uniprot_ids
    ]
    
    return result[0] if len(result) == 1 else result


def collect(uniprot_ids, *features):
    """
    Collects data about one or more UniProt IDs.
    
    :param str,list uniprot_ids:
        One or more UniProt IDs.
    :param *str,list features:
        Features to query: these must be method (property) names of the
        ``UniprotProtein`` class. E.g. ``['ac', 'genesymbol', 'function']``.
    
    :return:
        A ``collections.OrderedDict`` object with feature names as keys and
        list of values for each UniProt ID as values.
    """
    
    resources = [
        UniprotProtein(uniprot_id)
        for uniprot_id in uniprot_ids
    ]
    
    if 'ac' not in features:
        
        features = ['ac'] + list(*features)
    
    table = collections.OrderedDict(
        (
            feature_name,
            [
                getattr(resource, feature_name)
                for resource in resources
            ]
        )
        for feature_name in features
    )
    
    return table


def features_table(
        uniprot_ids,
        *features,
        width = 40,
        maxlen = 180,
        tablefmt = 'fancy_grid',
        **kwargs
    ):
    """
    Returns a table with the requested features of a list of UniProt IDs.
    The underlying table formatting module is ``tabulate``, a versatile
    module to export various ascii tables as well as HTML or LaTeX --
    check the docs for formatting options:
    https://github.com/astanin/python-tabulate
    
    :param **kwargs:
        Passed to ``tabulate.tabulate``.
    
    :return:
        The table as a string.
    """
    
    tbl = collect(uniprot_ids, *features)
    
    return common.table_format(
        tbl,
        width = width,
        maxlen = maxlen,
        tablefmt = tablefmt,
        **kwargs
    )


def print_features(
        uniprot_ids,
        *features,
        width = 40,
        maxlen = 200,
        tablefmt = 'fancy_grid',
        **kwargs
    ):
    """
    Prints a table with the requested features of a list of UniProt IDs.
    The underlying table formatting module is ``tabulate``, a versatile
    module to export various ascii tables as well as HTML or LaTeX --
    check the docs for formatting options:
    https://github.com/astanin/python-tabulate
    
    :param **kwargs:
        Passed to ``tabulate.tabulate``.
    
    :return:
        None.
    """
    
    sys.stdout.write(
        features_table(
            uniprot_ids,
            *features,
            width = width,
            maxlen = maxlen,
            tablefmt = tablefmt,
            **kwargs
        )
    )
    sys.stdout.write(os.linesep)
    sys.stdout.flush()


def info(*uniprot_ids, **kwargs):
    """
    Prints a table with the most important (or the requested) features of a
    list of UniProt IDs.
    """
    
    if (
        len(uniprot_ids) == 1 and
        isinstance(uniprot_ids, common.list_like)
    ):
        
        uniprot_ids = uniprot_ids[0]
    
    features = (
        kwargs['features']
            if 'features' in kwargs else
        (
            'ac',
            'genesymbol',
            'length',
            'weight',
            'full_name',
            'function',
            'keywords',
            'subcellular_location',
        )
    )
    
    print_features(
        uniprot_ids,
        *features,
        **kwargs
    )