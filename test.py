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
                "query": {"match": {"intervention_browse": "lung adenocarcinoma"}},
                "size": 10000,
            },
        )

        # body={"query": {"match": {"detailed_description": "carcinoma"}}},
        # body={"query": {"match": {"id_info": "NCT00001431"}}},

        for r in res["hits"]["hits"]:
            # print(r["_source"]["id_info"])
            with open("carcinoma", 'a') as f:
                f.write("{}\n".format(r["_source"]["id_info"]))

if __name__ == "__main__":
    testObject = Test()
    # testObject.getCount()
    testObject.searchSingle()
