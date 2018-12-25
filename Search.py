import json
import os
import sys

import xmltodict
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from pyes import *

from Config import Conf


class IRSearch(object):
    def __init__(self):
        self.conf = Conf()
        self.xml_path = self.conf.getConfig('path', 'xml_path')
        self.index_name = self.conf.getConfig('search', 'index_name')
        self.doc_type = self.conf.getConfig('search', 'doc_type')
        self.es = Elasticsearch()
        self.search_body = {}
        self.search_type_support = ['match_all', 'term', 'terms',
                                    'match', 'multi_match', 'bool', 'range', 'prefix', 'wildcard']
        self.search_type_model = self.conf.getSeachModel()
        self.conn = ES('127.0.0.1:9200')
        self.search_result = None
        
        self.conn.default_indices = [self.index_name]

    def makeQuery(self, searchtype, searchfield, keyword, is_sort=False, is_aggs=False, is_multi_match=False, use_bool=""):
        if searchtype not in self.search_type_support:
            print('Ops, your search type is not supported')
            print('Supported search types:\n')
            print(self.search_type_support)
            return
        self.search_body = self.search_type_model[searchtype]
        if is_multi_match:
            self.search_body["query"][searchtype] = {
                "query": keyword,
                "fields": searchfield
            }
        elif use_bool:
            self.search_body["query"][searchtype][use_bool] = [{
                "term": {
                    searchfield: keyword
                }
            }]
        else:
            self.search_body["query"][searchtype][searchfield] = keyword

        print(self.search_body)
        return self.search_body

    # I don't know what I am doing because I'm an idiot.
    def Query(self, searchtype, searchfield, keyword, is_sort=False, is_aggs=False, is_multi_match=False, use_bool=""):
        query_body = self.makeQuery(
            searchtype, searchfield, keyword, is_sort, is_aggs, is_multi_match, use_bool)
        result = self.es.search(index=self.index_name,
                                doc_type=self.doc_type, body=query_body)
        return result

    def querySingle(self, searchfield, keyword):
        q = TermQuery(searchfield, keyword)
        self.search_result = self.conn.search(query=q)
    

