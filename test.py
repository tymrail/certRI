import json
import os
import sys

import xmltodict
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

import DataProcessing
import Relevance
import Search
from Config import Conf


class Test(object):
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

    def getCount(self):
        print(self.es.count(index=self.index_name, doc_type=self.doc_type))


if __name__ == "__main__":
    testObject = Test()
    testObject.getCount()