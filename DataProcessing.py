import json
import os
import sys

import nltk
import xmltodict
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from Config import Conf
from utils import NormalAge


class DataPreprocessing(object):
    def __init__(self):
        self.conf = Conf()
        self.xml_path = self.conf.getConfig('path', 'xml_path')
        self.index_name = self.conf.getConfig('search', 'index_name')
        self.doc_type = self.conf.getConfig('search', 'doc_type')
        self.es = Elasticsearch()
        self.fields = self.conf.getImportant()
        # self.mapping = self.conf.getMapping()

        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)
        self.es.indices.create(index=self.index_name)
        # self.es.indices.put_mapping(index=self.index_name, doc_type=self.doc_type, body=self.mapping)
        print('created index:' + self.index_name)

    def xml2json(self, xmlpath):
        with open(xmlpath, 'r') as xmlf:
            xml_str = xmlf.read()
            dict_str = xmltodict.parse(xml_str)
            # json_str = json.dumps(dict_str)
            return dict_str

    def oswalk(self):
        count = 0
        for os_set in os.walk(self.xml_path, topdown=True):
            for filename in os_set[2]:
                try:
                    filepath = os.path.join(os_set[0], filename)
                    json_data = self.xml2json(filepath)

                    cleaned_json_data = {}

                    for field in self.fields:
                        if field in json_data["clinical_study"]:
                            if len(self.fields[field]) > 1 and not isinstance(json_data["clinical_study"][field], str):
                                cleaned_json_data[field] = json_data["clinical_study"][field][self.fields[field]]
                            else:
                                cleaned_json_data[field] = json_data["clinical_study"][field]

                    if "eligibility" in cleaned_json_data:
                        cleaned_json_data["eligibility"] = NormalAge(cleaned_json_data["eligibility"])

                    self.es.index(index=self.index_name, body=cleaned_json_data,
                                    doc_type=self.doc_type)

                    count += 1
                    if count % 1000 == 0:
                        print('Already finished:' + str(count))
                except KeyboardInterrupt:
                    print('Interrupted')
                    try:
                        sys.exit(0)
                    except SystemExit:
                        os._exit(0)
                except Exception as e:
                    print(e)
                    with open('errorxml.txt', 'a') as f:
                        f.write(str(filepath) + '\n')
                    print('Error in ', str(filename))


if __name__ == "__main__":
    DP = DataPreprocessing()
    DP.oswalk()
