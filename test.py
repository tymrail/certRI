import json
import os
import pickle
import pprint
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
        self.xml_path = self.conf.getConfig("path", "xml_path")
        self.index_name = self.conf.getConfig("search", "index_name")
        self.doc_type = self.conf.getConfig("search", "doc_type")
        self.es = Elasticsearch(timeout=30, max_retries=10, retry_on_timeout=True)
        self.search_body = {}
        self.search_type_support = [
            "match_all",
            "term",
            "terms",
            "match",
            "multi_match",
            "bool",
            "range",
            "prefix",
            "wildcard",
        ]
        self.search_type_model = self.conf.getSeachModel()

    def getCount(self):
        print(self.es.count(index=self.index_name, doc_type=self.doc_type))

    def searchSingle(self):
        res = self.es.search(
            index=self.index_name,
            doc_type=self.doc_type,
            body={
                "query": {"match": {"id_info": "NCT02065063"}},
                "size": 10000,
            },
        )

        # body={"query": {"match": {"detailed_description": "carcinoma"}}},
        # body={"query": {"match": {"id_info": "NCT00001431"}}},

        for r in res["hits"]["hits"]:
            print(r["_source"])
            with open("carcinoma", 'a') as f:
                f.write("{}\n".format(r["_source"]["id_info"]))

    def getPickles(self, pickle_path):
        with open(pickle_path, 'rb') as pf:
            data = pickle.load(pf)
            # pprint.pprint(data)
            return data

if __name__ == "__main__":
    testObject = Test()
    # testObject.getCount()
    testObject.searchSingle()
    # d = testObject.getPickles("pickles/mesh_dict.pickle")
