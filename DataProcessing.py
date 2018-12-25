import json
import os
import sys

import nltk
import xmltodict
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from gensim import corpora
from gensim.summarization import bm25
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer

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
        self.gensim_fields = self.conf.getGenFields()
        # self.mapping = self.conf.getMapping()
        self.dict = None
        self.sentence_list = []
        self.tokenizer = RegexpTokenizer(r'\w+')
        self.lem = WordNetLemmatizer()
        self.stopwords = set(stopwords.words('english'))
        self.tokens_list = []
        self.corpus = None

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

    def tokenize(self, doc):
        raw_tokens = self.tokenizer.tokenize(doc.lower())
        lem_tokens = [self.lem.lemmatize(token) for token in raw_tokens]
        lem_tokens_without_stopword = filter(lambda i: i not in self.stopwords, lem_tokens)
        return list(lem_tokens_without_stopword)
    
    def getDict(self):
        for sentence in self.sentence_list:
            tokens = self.tokenize(sentence)
            self.tokens_list.append(tokens)
        self.dict = corpora.Dictionary(self.tokens_list)

    def getModel(self):
        self.corpus = [self.dict.doc2bow(text) for text in self.tokens_list]
        # self.bm25Model = bm25.BM25(self.corpus)
        # self.average_idf = sum(map(lambda k: float(self.bm25Model.idf[k]), self.bm25Model.idf.keys())) / len(self.bm25Model.idf.keys())

    def saveModel(self):
        self.dict.save("/models/trec.dict")
        corpora.MmCorpus.serialize("/models/trec.mm", self.corpus)

    def oswalk(self):
        count = 0
        for os_set in os.walk(self.xml_path, topdown=True):
            for filename in os_set[2]:
                try:
                    filepath = os.path.join(os_set[0], filename)
                    json_data = self.xml2json(filepath)

                    cleaned_json_data = {}
                    gen_sentence = ''

                    for field in self.fields:
                        if field in json_data["clinical_study"]:
                            if len(self.fields[field]) > 1 and not isinstance(json_data["clinical_study"][field], str):
                                cleaned_json_data[field] = json_data["clinical_study"][field][self.fields[field]]
                            else:
                                cleaned_json_data[field] = json_data["clinical_study"][field]

                            if field in self.gensim_fields:
                                gen_sentence += str(json_data["clinical_study"][field]) + ' .'
                    if "eligibility" in cleaned_json_data:
                        cleaned_json_data["eligibility"] = NormalAge(cleaned_json_data["eligibility"])

                    self.es.index(index=self.index_name, body=cleaned_json_data,
                                    doc_type=self.doc_type)
                    self.sentence_list.append(gen_sentence)

                    count += 1                        
                    if count % 5000 == 0:
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
        # self.getDict()
        # self.getModel()
        # self.saveModel()
