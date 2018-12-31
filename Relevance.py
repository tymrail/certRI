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

# class BM25(object):
#     def __init__(self, *args, **kwargs):
#         self.tokenizer = RegexpTokenizer(r'\w+')
#         self.lem = WordNetLemmatizer()
#         self.stopwords = set(stopwords.words('english'))
#         self.dict = None
#         self.corpus = None
#         self.bm25model = None

#     def cleanData(self, doc):
#         raw_tokens = self.tokenizer.tokenize(doc.lower())
#         lem_tokens = [self.lem.lemmatize(token) for token in raw_tokens]
#         lem_tokens_without_stopword = filter(lambda i: i not in self.stopwords, lem_tokens)
#         return list(lem_tokens_without_stopword)

#     def getReady(self, tokens_list):
#         self.dict = corpora.Dictionary(tokens_list)

#         print('Dictionary Length:', str(len(self.dict)))

#         self.corpus = tokens_list


# class dataClean(object):
#     def __init__(self, xml_path):
#         self.xml_path = xml_path
#         self.doc_list = []
#         self.corpus = None
    
#     def oswalk(self):
#         for root, _, files in os.walk(self.xml_path):
#             for xml in files:
#                 full_path = os.path.join(root, xml)
#                 with open(full_path, 'r') as f:
#                     xmldata = f.read()
#                     dictdata = xmltodict.parse(xmldata)
#                     self.doc_list.append(dictdata)
                    

class calculateBM25(object):
    def __init__(self, datasets, query_str, query_id, name="noncut"):
        self.datasets = datasets
        self.query = query_str.split(' ')
        self.query_id = query_id
        self.corpus = []
        self.tokenizer = RegexpTokenizer(r'\w+')
        self.dictionary = None
        self.sorted_result = []
        self.bm25Model = None
        self.name = name

    def getWeightedData(self):
        score_max = self.datasets[0]["_score"]

        for data in self.datasets:
            # print(data)
            # default
            # brief_title = (data["_source"]["brief_title"] + ' ') * 3
            # official_title = (data["_source"]["official_title"] + ' ') * 3
            # detailed_description = (data["_source"]["detailed_description"] + ' ') * 1
            # brief_summary = (data["_source"]["brief_summary"] + ' ') * 1
            # criteria = (data["_source"]["eligibility"]["criteria"]["textblock"] + ' ') * 2
            # keywords = (' '.join(data["_source"]["keyword"]) + ' ') * 3
            # condition = (' '.join(data["_source"]["condition"]) + ' ') * 2
            
            # ss
            brief_title = (data["_source"]["brief_title"] + ' ') * 4
            official_title = (data["_source"]["official_title"] + ' ') * 3
            detailed_description = (data["_source"]["detailed_description"] + ' ') * 1
            brief_summary = (data["_source"]["brief_summary"] + ' ') * 1
            criteria = (data["_source"]["eligibility"]["criteria"]["textblock"] + ' ') * 3
            keywords = (' '.join(data["_source"]["keyword"]) + ' ') * 4
            condition = (' '.join(data["_source"]["condition"]) + ' ') * 2

            # official_title = (data["_source"]["official_title"] + ' ') * 2
            # detailed_description = (data["_source"]["detailed_description"] + ' ') * 1
            # brief_summary = (data["_source"]["brief_summary"] + ' ') * 2
            # criteria = (data["_source"]["eligibility"]["criteria"]["textblock"] + ' ') * 3
            # keywords = (' '.join(data["_source"]["keyword"]) + ' ') * 4
            # condition = (' '.join(data["_source"]["condition"]) + ' ') * 2
            
            final_data = brief_title + official_title + detailed_description + brief_summary + criteria + keywords + condition
            self.corpus.append(self.tokenizer.tokenize((final_data)))

            self.sorted_result.append({"id": self.query_id,"id_info": data["_source"]["id_info"], "score": data["_score"] / score_max})

    def getModel(self):
        self.dictionary = corpora.Dictionary(self.corpus)
        self.doc_vectors = [self.dictionary.doc2bow(text) for text in self.corpus]
        self.bm25Model = bm25.BM25(self.corpus)
        self.average_idf = sum(map(lambda k: float(self.bm25Model.idf[k]), self.bm25Model.idf.keys())) / len(self.bm25Model.idf.keys())

    def calculateNewResult(self):
        bm25scores = self.bm25Model.get_scores(self.query, self.average_idf)
        bm25score_max = max(bm25scores)
        bm25scores_norm = [s / bm25score_max for s in bm25scores]

        for i in range(10):
            new_result = []
            for res_set, bm25s in zip(self.sorted_result, bm25scores_norm):
                new_res_set = {"id":res_set["id"], "id_info":res_set["id_info"], "score":res_set["score"] * i / 10 + bm25s * (10 - i) /10}
                new_result.append(new_res_set)
            
            filename = 'trec_eval/eval/DE_' + str(i) + '_BM25_' + str(10 - i) + '_' + self.name + '.txt'
            sorted_new_result = sorted(new_result, key = lambda k:(k.get("score")), reverse=True)

            rank = 1
            with open(filename, 'a') as f:
                for r in sorted_new_result:
                    f.write(
                        "{} Q0 {} {} {} certRI\n".format(
                            r["id"],
                            r["id_info"],
                            rank,
                            round(r["score"], 4),
                        )
                    )
                    rank += 1
            print("Finished {}".format(filename))

    def run(self):
        self.getWeightedData()
        self.getModel()
        self.calculateNewResult()

                





        

    
    


        
