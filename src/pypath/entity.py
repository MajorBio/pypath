#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#  This file is part of the `pypath` python module
#  Exports tables for webservice.
#
#  Copyright (c) 2014-2019 - EMBL
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


import pypath.common as common
import pypath.intera as intera
import pypath.session_mod as session_mod


class Entity(session_mod.Logger):
    
    
    def __init__(self, identifier, entity_type = None, id_type = None):
        
        self.identifier = identifier
        self.entity_type = entity_type or self.get_entity_type()
        self.id_type = id_type
    
    
    @staticmethod
    def entity_name_str(entity):
        
        return (
            entity
                if isinstance(entity, common.basestring) else
            str(entity)
        )
    
    
    @classmethod
    def igraph_vertex_name(cls, igraph_v):
        
        return cls.entity_name_str(igraph_v['name'])
    
    
    @staticmethod
    def igraph_vertex_label(igraph_v):
        
        return igraph_v['label']
    
    
    @classmethod
    def igraph_vertex_name_label(cls, igraph_v):
        
        return (
            cls.igraph_vertex_name(igraph_v),
            cls.igraph_vertex_label(igraph_v),
        )
    
    
    @staticmethod
    def _is_protein(key):
        
        return (
            isinstance(key, common.basestring) and
            not key.startswith('MIMAT') and
            not key.startswith('COMPLEX')
        )
    
    
    @staticmethod
    def _is_mirna(key):
        
        return (
            isinstance(key, common.basestring) and
            key.startswith('MIMAT')
        )
    
    
    @staticmethod
    def _is_complex(key):
        
        return isinstance(key, intera.Complex) or (
            isinstance(key, common.basestring) and
            key.startswith('COMPLEX')
        )
    
    
    @classmethod
    def _get_entity_type(cls, key):
        
        return (
            'complex'
                if cls._is_complex(key) else
            'mirna'
                if cls._is_mirna(key) else
            'protein'
        )
    
    
    def is_protein(self):
        
        return self._is_protein(self.identifier)
    
    
    def is_mirna(self):
        
        return self._is_mirna(self.identifier)
    
    
    def is_complex(self):
        
        return self._is_complex(self.identifier)
    
    
    def get_entity_type(self):
        
        return self._get_entity_type(self.identifier)
    
    
    def __eq__(self, other):
        
        return (
            hasattr(other, 'identifier') and
            self.identifier == other.identifier
        )
