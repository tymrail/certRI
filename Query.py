import json

import xmltodict
from elasticsearch import Elasticsearch

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import PorterStemmer

from Config import Conf

import pickle

from Relevance import calculateBM25


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

        self.filter = (
            [28, 29, 25, 22, 6, 7],
            [26, 11, 1, 18, 21, 4],
            [19, 24, 27, 30, 12, 23],
            [13, 14, 3, 16, 8, 9],
            [15, 20, 5, 10, 17, 2],
        )

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

    def query(self, single_query, name='non_cut'):       
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
        # with age and gender: p5: 0.3655 p10:0.3241 p15:0.2920

        # query_base = (single_query["disease"] + ' ') * 3
        # query_gene = (single_query["gene"].replace("(", " ").replace(")", " ").replace(",", "").replace(";", "") + ' ') * 2

        # query_body = {
        #     "query": {
        #         "multi_match": {
        #             "query": (query_base + ' ' + query_gene).lower(),
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
        # P5: 0.4069  P10: 0.3276 P15: 0.2736

        query_base = (single_query["disease"] + " ") * 3
        query_gene = (
            single_query["gene"]
            .replace("(", " ")
            .replace(")", " ")
            .replace(",", "")
            .replace(";", "")
            + " "
        ) * 2

        query_body = {
            "query": {
                "multi_match": {
                    "query": (query_base + " " + query_gene).lower(),
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

        filter_result = []

        for qr in query_result:
            # 过滤年龄不符合的情况
            if "eligibility" in qr["_source"]:
                qr_eli = qr["_source"]["eligibility"]
                if float(qr_eli["minimum_age"]) > single_query["age"] or single_query[
                    "age"
                ] > float(qr_eli["maximum_age"]):
                    continue
                if qr_eli["gender"].lower().strip() not in [
                    single_query["gender"].lower(),
                    "all",
                    "All",
                ]:
                    # print(qr_eli["gender"].lower())
                    # print(single_query["gender"].lower())
                    continue
                filter_result.append(qr)

        bm25_Object = calculateBM25(
            filter_result, (query_base + " " + query_gene).lower(), single_query["id"], name
        )
        bm25_Object.run()

        # print(query_result)
        score_max = query_result[0]["_score"]
        rank = 1
        with open("trec_eval/eval/res_{}.txt".format(name), "a") as f:
            try:
                for qr in filter_result:
                    # 按照要求格式写文件
                    f.write(
                        "{} Q0 {} {} {} certRI\n".format(
                            single_query["id"],
                            qr["_source"]["id_info"],
                            rank,
                            round(qr["_score"] / score_max, 4),
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
            # self.query(single_query)

    def run_with_5(self):
        data_5 = [
            [
                {'id': '28', 'disease': 'Pancreatic ductal adenocarcinoma', 'gene': 'ERBB3', 'age': 26645, 'gender': 'female', 'other': 'Whipple, FNA'},
                {'id': '29', 'disease': 'Ampullary carcinoma', 'gene': 'KRAS', 'age': 22265, 'gender': 'male', 'other': 'None'},
                {'id': '25', 'disease': 'Lung adenocarcinoma', 'gene': 'MET Amplification', 'age': 17520, 'gender': 'male', 'other': 'Emphysema'},
                {'id': '22', 'disease': 'Lung cancer', 'gene': 'ERBB2 Amplification', 'age': 25550, 'gender': 'male', 'other': 'Arthritis'},
                {'id': '6', 'disease': 'Melanoma', 'gene': 'NRAS (Q61K)', 'age': 20075, 'gender': 'male', 'other': 'Hypertension'},
                {'id': '7', 'disease': 'Lung cancer', 'gene': 'EGFR (L858R)', 'age': 18250, 'gender': 'female', 'other': 'Lupus'}
            ],
            [
                {'id': '26', 'disease': 'Breast cancer', 'gene': 'NRAS Amplification', 'age': 12775, 'gender': 'female', 'other': 'None'},
                {'id': '11', 'disease': 'Gastric cancer', 'gene': 'PIK3CA (E545K)', 'age': 19710, 'gender': 'male', 'other': 'Depression'},
                {'id': '1', 'disease': 'Liposarcoma', 'gene': 'CDK4 Amplification', 'age': 13870, 'gender': 'male', 'other': 'GERD'},
                {'id': '18', 'disease': 'Pancreatic cancer', 'gene': 'CDK6 Amplification', 'age': 17520, 'gender': 'male', 'other': 'None'},
                {'id': '21', 'disease': 'Lung adenocarcinoma', 'gene': 'ALK Fusion', 'age': 23360, 'gender': 'female', 'other': 'Emphysema'},
                {'id': '4', 'disease': 'Breast cancer', 'gene': 'FGFR1 Amplification, PTEN (Q171)', 'age': 24455, 'gender': 'female', 'other': 'Depression'}
            ],
            [
                {'id': '19', 'disease': 'Colorectal cancer', 'gene': 'FGFR1 Amplification', 'age': 12775, 'gender': 'female', 'other': 'None'},
                {'id': '24', 'disease': 'Lung cancer', 'gene': 'NTRK1', 'age': 21170, 'gender': 'female', 'other': 'Depression, Hypertension, Diabetes'},
                {'id': '27', 'disease': 'Pancreatic adenocarcinoma', 'gene': 'KRAS, TP53', 'age': 17885, 'gender': 'female', 'other': 'None'},
                {'id': '30', 'disease': 'Pancreatic adenocarcinoma', 'gene': 'RB1, TP53, KRAS', 'age': 20805, 'gender': 'female', 'other': 'None'},
                {'id': '12', 'disease': 'Colon cancer', 'gene': 'BRAF (V600E)', 'age': 12775, 'gender': 'male', 'other': 'None'},
                {'id': '23', 'disease': 'Breast cancer', 'gene': 'PTEN Loss', 'age': 19710, 'gender': 'female', 'other': 'Congestive Heart Failure'}
            ],
            [
                {'id': '13', 'disease': 'Cholangiocarcinoma', 'gene': 'BRCA2', 'age': 26280, 'gender': 'male', 'other': 'Diabetes'},
                {'id': '14', 'disease': 'Cholangiocarcinoma', 'gene': 'IDH1 (R132H)', 'age': 23360, 'gender': 'male', 'other': 'Neuropathy'},
                {'id': '3', 'disease': 'Meningioma', 'gene': 'NF2 (K322), AKT1(E17K)', 'age': 16425, 'gender': 'female', 'other': 'None'},
                {'id': '16', 'disease': 'Pancreatic cancer', 'gene': 'CDKN2A', 'age': 19710, 'gender': 'male', 'other': 'Diabetes, Hypertension'},
                {'id': '8', 'disease': 'Lung cancer', 'gene': 'EML4-ALK Fusion transcript', 'age': 18980, 'gender': 'male', 'other': 'Hypertension, Osteoarthritis'},
                {'id': '9', 'disease': 'Gastrointestinal stromal tumor', 'gene': 'KIT Exon 9 (A502_Y503dup)', 'age': 17885, 'gender': 'female', 'other': 'None'}
            ],
            [
                {'id': '15', 'disease': 'Cervical cancer', 'gene': 'STK11', 'age': 9490, 'gender': 'female', 'other': 'None'},
                {'id': '20', 'disease': 'Liposarcoma', 'gene': 'MDM2 Amplification', 'age': 9490, 'gender': 'male', 'other': 'None'},
                {'id': '5', 'disease': 'Melanoma', 'gene': 'BRAF (V600E), CDKN2A Deletion', 'age': 16425, 'gender': 'female', 'other': 'None'},
                {'id': '10', 'disease': 'Lung adenocarcinoma', 'gene': 'KRAS (G12C)', 'age': 22265, 'gender': 'female', 'other': 'Hypertension, Hypercholesterolemia'},
                {'id': '17', 'disease': 'Prostate cancer', 'gene': 'PTEN Inactivating', 'age': 29565, 'gender': 'male', 'other': 'Hypertension, Depression'},
                {'id': '2', 'disease': 'Colon cancer', 'gene': 'KRAS (G13D), BRAF (V600E)', 'age': 18980, 'gender': 'male', 'other': 'Type II Diabetes, Hypertension'}
            ]
        ]
        for i in range(5):
            for single_query in data_5[i]:
                self.query(single_query, name = 'cut_' + str(i+1))

if __name__ == "__main__":
    q = Query()
    # q.extract_query()
    # q.run()
    q.run_with_5()
