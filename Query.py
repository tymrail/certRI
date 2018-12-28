import json

import xmltodict
from elasticsearch import Elasticsearch

from Config import Conf


class Query(object):
    def __init__(self):
        self.conf = Conf()
        self.query_xml_path = self.conf.getConfig("path", "query_xml_path")
        self.index_name = self.conf.getConfig("search", "index_name")
        self.doc_type = self.conf.getConfig("search", "doc_type")
        self.es = Elasticsearch(timeout=30, max_retries=10, retry_on_timeout=True)
        self.fields = self.conf.getImportant()
        self.extracted = []

    def xml2json(self, xmlpath):
        with open(xmlpath, "r") as xmlf:
            xml_str = xmlf.read()
            dict_str = xmltodict.parse(xml_str)
            # json_str = json.dumps(dict_str)
            return dict_str

    def extract_query(self):
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

    def query(self, single_query):
        gender_lst = ["male", "female"]
        must_not_gender = gender_lst[abs(gender_lst.index(single_query["gender"]) - 1)]
        # query_body = {
        #     "query": {
        #         "bool": {
        #             "must": [
        #                 {
        #                     "multi_match": {
        #                         "query": single_query["disease"],
        #                         "fields": [
        #                             "brief_title",
        #                             "detailed_description",
        #                             "official_title",
        #                             "intervention",
        #                             "intervention_browse",
        #                             "keyword",
        #                             "condition",
        #                             "criteria",
        #                         ],
        #                     }
        #                 },
        #             ],
        #             "must_not": [{"term": {"gender": must_not_gender}}],
        #         }
        #     },
        #     "size": 1500,
        # }
        query_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"brief_title": single_query["disease"]}},
                        {"match": {"brief_summary": single_query["disease"]}},
                        {"match": {"detailed_description": single_query["disease"]}},
                        {"match": {"official_title": single_query["disease"]}},
                        {"match": {"intervention": single_query["disease"]}},
                        {"match": {"intervention_browse": single_query["disease"]}},
                        {"match": {"keyword": single_query["disease"]}},
                        {"match": {"condition": single_query["disease"]}},
                        {"match": {"criteria": single_query["disease"]}},
                    ],
                    "must_not": [{"term": {"gender": must_not_gender}}],
                }
            },
            "size": 1500,
        }

        query_result = self.es.search(
            index=self.index_name, doc_type=self.doc_type, body=query_body
        )["hits"]["hits"]

        # print(query_result)
        score_max = query_result[0]['_score']
        rank = 1
        with open("result/output_4.txt", "a") as f:
            try:
                for qr in query_result:
                    if "eligibility" in qr["_source"]:
                        qr_eli = qr["_source"]["eligibility"]
                        if float(qr_eli["minimum_age"]) > single_query[
                            "age"
                        ] or single_query["age"] > float(qr_eli["maximum_age"]):
                            continue
                    f.write(
                        "{}\tQ0\t{}\t{}\t{}\tcertRI\n".format(
                            single_query["id"],
                            qr["_source"]["id_info"],
                            rank,
                            round(qr["_score"]/score_max, 4),
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
