#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  This file is part of the `pypath` python module.
#  Provides a high level interface for managing builds of the
#  OmniPath databases.
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


import pypath.omnipath.aux as omnipath_aux
import pypath.share.session as session

_logger = session.Logger(name = 'omnipath_db_build')
_log = _logger._log


def build(dbclass, dbdef):
    """
    Builds a database following the instructions in a ``DatabaseDefinition``
    object, using the database class or method ``dbclass``.
    
    This is not the preferred method to get a database instance.
    Unless there is a strong reason, both built in and user defined databases
    should be managed by the ``pypath.omnipath.app`` module.
    """
    
    dbclass = dbclass if callable(dbclass) else dbclass.get_class()
    
    _log(
        'Building database `%s` (class %s).' % (
            dbdef.label,
            dbclass.label,
        )
    )
    
    build_method = (
        dbclass
            if not dbdef.get('init') else
        getattr(dbclass, dbdef.get('init'))
    )
    
    build_args = dbdef.get('args') or {}
    
    db = build_method(**build_args)
    
    prep = dbdef.get('prepare') or {}
    
    for var, method in prep.items():
        
        if isinstance(method, dict):
            
            prep_method_args = method['args']
            method = method['method']
            
        else:
            
            prep_method_args = {}
        
        if callable(method):
            
            locals()[var] = method()
            
        else:
            
            method_host = (
                db
                    if hasattr(db, method) else
                omnipath_aux
                    if hasattr(omnipath_aux, method) else
                None
            )
            
            if method_host:
                
                locals()[var] = (
                    getattr(method_host, method)(**prep_method_args)
                )
                
            else:
                
                _log('Could not find preparatory method `%s`.' % method)
    
    workflow = dbdef.get('workflow') or {}
    
    for step in workflow:
        
        method = step['method']
        args = dict(
            (
                argname,
                locals()[val] if val in locals() else val
            )
            for argname, val in step['args']
        )
        
        getattr(db, method)(**args)
    
    _log(
        'Finished building database `%s` (class %s).' % (
            dbdef.label,
            dbclass.label,
        )
    )
    
    return db
