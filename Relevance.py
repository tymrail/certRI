import codecs
from gensim import corpora
from gensim.summarization import bm25
import os
import re
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
import xmltodict


class BM25(object):
    def __init__(self, *args, **kwargs):
        self.tokenizer = RegexpTokenizer(r'\w+')
        self.lem = WordNetLemmatizer()
        self.stopwords = set(stopwords.words('english'))
        self.dict = None
        self.corpus = None
        self.bm25model = None

    def cleanData(self, doc):
        raw_tokens = self.tokenizer.tokenize(doc.lower())
        lem_tokens = [self.lem.lemmatize(token) for token in raw_tokens]
        lem_tokens_without_stopword = filter(lambda i: i not in self.stopwords, lem_tokens)
        return list(lem_tokens_without_stopword)

    def getReady(self, tokens_list):
        self.dict = corpora.Dictionary(tokens_list)

        print('Dictionary Length:', str(len(self.dict)))

        self.corpus = tokens_list


class dataClean(object):
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.doc_list = []
        self.corpus = None
    
    def oswalk(self):
        for root, _, files in os.walk(self.xml_path):
            for xml in files:
                full_path = os.path.join(root, xml)
                with open(full_path, 'r') as f:
                    xmldata = f.read()
                    dictdata = xmltodict.parse(xmldata)
                    self.doc_list.append(dictdata)
                    
                    
        
