import json

import xmltodict
from elasticsearch import Elasticsearch

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import PorterStemmer

from Config import Conf

import pickle


class Query(object):
    def __init__(self):
        self.conf = Conf()
        self.query_xml_path = self.conf.getConfig("path", "query_xml_path")
        self.index_name = self.conf.getConfig("search", "index_name")
        self.doc_type = self.conf.getConfig("search", "doc_type")
        self.meshDict = self.getPickles(self.conf.getConfig("path", "dict_pickle_path"))
        self.es = Elasticsearch(timeout=30, max_retries=10, retry_on_timeout=True)
        # 设定es的超时时限为30秒，默认为10秒
        # 最大重试次数为10次
        # 防止因数据量太大导致的超时
        self.fields = self.conf.getImportant()
        self.extracted = []

        self.tokenizer = RegexpTokenizer(r"\w+")
        self.lem = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        self.stopwords = set(stopwords.words("english"))

    def getPickles(self, pickle_path):
        with open(pickle_path, "rb") as pf:
            data = pickle.load(pf)
            return data

    def xml2json(self, xmlpath):
        with open(xmlpath, "r") as xmlf:
            xml_str = xmlf.read()
            dict_str = xmltodict.parse(xml_str)
            # json_str = json.dumps(dict_str)
            return dict_str

    def extract_query(self):
        # 处理查询字段
        query_xml_data = self.xml2json(self.query_xml_path)["topics"]["topic"]
        for q in query_xml_data:
            new_query = {
                "id": q["@number"],
                "disease": q["disease"],
                "gene": q["gene"],
                "age": int(q["demographic"].split("-")[0]) * 365,
                "gender": q["demographic"].split(" ")[-1],
                "other": q["other"],
            }
            self.extracted.append(new_query)
        with open("query.json", "w") as f:
            f.write(json.dumps(self.extracted, indent=4))

    def cleanData(self, doc):
        raw_tokens = self.tokenizer.tokenize(doc.lower())
        lem_tokens = [self.stemmer.stem(token) for token in raw_tokens]
        lem_tokens = [
            token for token in lem_tokens if not token.isdigit() and len(token) > 1
        ]
        lem_tokens_without_stopword = filter(
            lambda i: i not in self.stopwords, lem_tokens
        )
        return list(lem_tokens_without_stopword)

    def query(self, single_query):
        gender_lst = ["male", "female"]
        must_not_gender = gender_lst[abs(gender_lst.index(single_query["gender"]) - 1)]
        # 性别分为male，female和All三种，得到不用的一种

        query_keywords = single_query["disease"].lower().split(" ")
        relevence = single_query["disease"].lower().split(" ")

        for qk in query_keywords:
            # qk = qk.lower()
            if qk in self.meshDict and qk not in [
                "cancer",
                "adenocarcinoma",
                "carcinoma",
            ]:
                relevence += self.meshDict[qk]

        if "mesh_numbers" in relevence:
            relevence.remove("mesh_numbers")
        relevence = list(set(self.cleanData(" ".join(relevence))))

        print(single_query["gene"].replace("(", " ").replace(")", " ").replace(",", ""))

        # for rl in relevence:
        #     if rl in ["mesh_numbers", "cancers", "non", "carcinomas", "tumors", "neoplasms", "pseudocysts", "cysts", "vipomas"]:
        #         # print(rl)
        #         relevence.remove(rl)

        relevence_str = " ".join(relevence)
        # print(relevence_str)

        # query_body = {
        #     "query": {
        #         "multi_match": {
        #             "query": (single_query["disease"] + ' ' + single_query["gene"].replace("(", " ").replace(")", " ").replace(",", "")).lower(),
        #             "type": "cross_fields",
        #             "fields": [
        #                 "brief_title",
        #                 "brief_summary",
        #                 "detailed_description",
        #                 "official_title",
        #                 "keyword",
        #                 "condition",
        #                 "eligibility.criteria.textblock",
        #             ],
        #         }
        #     },
        #     "size": 1000,
        # }
        # p5: 0.3586
        # p10:0.3138
        # p15:0.2704
        # with age: p5: 0.3586 p10:0.3172 p15:0.2805
        # with gender: p5: 0.3655 p10:0.3241 p15:0.2920

        query_body = {
            "query": {
                "multi_match": {
                    "query": (single_query["disease"] + ' ' + single_query["gene"].replace("(", " ").replace(")", " ").replace(",", "")).lower(),
                    "type": "cross_fields",
                    "fields": [
                        "brief_title",
                        "brief_summary",
                        "detailed_description",
                        "official_title",
                        "keyword",
                        "condition",
                        "eligibility.criteria.textblock",
                    ],
                }
            },
            "size": 1000,
        }

        # query_body = {
        #     "query": {
        #         "multi_match": {
        #             "query": (single_query["gene"].replace("(", " ").replace(")", " ").replace(",", "")).lower(),
        #             "type": "cross_fields",
        #             "fields": [
        #                 "brief_title",
        #                 "brief_summary",
        #                 "detailed_description",
        #                 "official_title",
        #                 "keyword",
        #                 "condition",
        #                 "eligibility.criteria.textblock",
        #             ],
        #         }
        #     },
        #     "size": 1000,
        # }

        # query_standard = (single_query["gene"].replace("(", " ").replace(")", " ").replace(",", "")).lower()

        # query_body = {
        #     "query": {
        #         "bool": {
        #             "should": [
        #                 {"match": {"brief_title": {"query": query_standard, "boost": 2}}},
        #                 {"match": {"official_title": {"query": query_standard, "boost": 2}}},
        #                 {"match": {"brief_summary": {"query": query_standard, "boost": 1}}},
        #                 {"match": {"detailed_description": {"query": query_standard, "boost": 1}}},
        #                 {"match": {"eligibility.criteria.textblock": {"query": query_standard, "boost": 5}}},
        #                 {"match": {"keyword": {"query": query_standard, "boost": 6}}},
        #                 {"match": {"condition": {"query": query_standard, "boost": 3}}},
        #             ],
        #             "must_not": [{"term": {"gender": must_not_gender}}],
        #         },
        #     },
        #     "size": 1500,
        # }
        # 这里的querybody需要再认真设计下，不同的查询方式对最终结果的MAP和P@10影响很大

        query_result = self.es.search(
            index=self.index_name, doc_type=self.doc_type, body=query_body
        )["hits"]["hits"]
        # 获得查询结果

        # print(query_result)
        # score_max = query_result[0]["_score"]
        rank = 1
        with open("trec_eval/eval/r40.txt", "a") as f:
            try:
                for qr in query_result:
                    # 过滤年龄不符合的情况
                    if "eligibility" in qr["_source"]:
                        qr_eli = qr["_source"]["eligibility"]
                        if float(qr_eli["minimum_age"]) > single_query["age"] or\
                            single_query["age"] > float(qr_eli["maximum_age"]):
                            continue
                        if qr_eli["gender"].lower().strip() not in [single_query["gender"].lower(), 'all', 'All']:
                            print(qr_eli["gender"].lower())
                            print(single_query["gender"].lower())
                            continue

                    # 按照要求格式写文件
                    f.write(
                        "{} Q0 {} {} {} certRI\n".format(
                            single_query["id"],
                            qr["_source"]["id_info"],
                            rank,
                            round(qr["_score"], 4),
                        )
                    )
                    rank += 1

                    if rank > 1000:
                        break

            except ValueError as _:
                print(qr["_source"]["eligibility"])
            except KeyError as ke:
                print(ke)
                print(qr["_source"])

        print("Relative docs:{}".format(rank - 1))

    def run(self):
        self.extract_query()
        for single_query in self.extracted:
            print(single_query)
            self.query(single_query)


if __name__ == "__main__":
    q = Query()
    # q.extract_query()
    q.run()
