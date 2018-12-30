import codecs
import os
import re
import sys

import nltk
import xmltodict
from gensim import corpora
from gensim.summarization import bm25
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer
from gensim.models import word2vec

from Config import Conf


class W2V(object):
    def __init__(self):
        self.tokenizer = RegexpTokenizer(r'\w+')
        self.lem = WordNetLemmatizer()
        self.stopwords = set(stopwords.words('english'))
        self.dict = None
        self.corpus = None
        self.bm25model = None
        self.docs_list = []
        self.conf = Conf()
        self.xml_path = self.conf.getConfig('path', 'xml_path')

    def cleanData(self, doc):
        raw_tokens = self.tokenizer.tokenize(doc.lower())
        lem_tokens = [self.lem.lemmatize(token) for token in raw_tokens]
        lem_tokens_without_stopword = filter(lambda i: i not in self.stopwords, lem_tokens)
        return list(lem_tokens_without_stopword)

    def xml2json(self, xmlpath):
        with open(xmlpath, "r") as xmlf:
            xml_str = xmlf.read()
            dict_str = xmltodict.parse(xml_str)
            # json_str = json.dumps(dict_str)
            return dict_str

    def extractUseful(self, dict_str):
        useful_list = []
        
        if "official_title" in dict_str["clinical_study"]:
            useful_list.append(dict_str["clinical_study"]["official_title"])
        else:
            useful_list.append(dict_str["clinical_study"]["brief_title"])
        
        if "brief_summary" in dict_str["clinical_study"]:
            useful_list.append(dict_str["clinical_study"]["brief_summary"]["textblock"])

        if "detailed_description" in dict_str["clinical_study"]:
            useful_list.append(dict_str["clinical_study"]["detailed_description"]["textblock"])

        if "eligibility" in dict_str["clinical_study"]:
            useful_list.append(dict_str["clinical_study"]["eligibility"]["criteria"]["textblock"])

        return ','.join(useful_list)

    def buildModel(self):
        model = word2vec.Word2Vec(sentences=self.docs_list, min_count=5, workers=4)
        model.save("models/w2v.model")
    
    def run(self):
        count = 0

        for root, _, files in os.walk(self.xml_path, topdown=True):
            for filename in files:
                try:
                    file_path = os.path.join(root, filename)
                    json_data = self.xml2json(file_path)

                    useful_str = self.extractUseful(json_data)
                    useful_tokens = self.cleanData(useful_str)

                    self.docs_list.append(useful_tokens)
                except KeyboardInterrupt:
                    # 处理ctrl+C中断程序的情况
                    print('Interrupted')
                    try:
                        sys.exit(0)
                    except SystemExit:
                        os._exit(0)
                except Exception as e:
                    print(e)
                    with open('error_w2v_xml.txt', 'a') as f:
                        f.write(str(file_path) + '\n')
                    print('Error in ', str(filename))
                
                count += 1
                if count % 2000 == 0:
                    print("Already finished {}".format(count))
        
        print("Start build model")
        self.buildModel()


if __name__ == "__main__":
    w2v = W2V()
    w2v.run()
