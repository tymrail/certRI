import json
import os
import sys

import nltk
import xmltodict
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import PorterStemmer

from Config import Conf
from utils import NormalAge


class DataPreprocessing(object):
    def __init__(self):
        self.conf = Conf()
        self.xml_path = self.conf.getConfig("path", "xml_path")
        self.index_name = self.conf.getConfig("search", "index_name")
        self.doc_type = self.conf.getConfig("search", "doc_type")
        # 读取设定

        self.tokenizer = RegexpTokenizer(r"\w+")
        self.lem = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        self.stopwords = set(stopwords.words("english"))

        self.es = Elasticsearch()
        self.fields = self.conf.getImportant()
        # self.mapping = self.conf.getMapping()

        # es的index和doc_type相当于mysql的db和table
        # 如果要创建的index已存在，则删除原有index
        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)

        # 创建index
        self.es.indices.create(index=self.index_name)
        # self.es.indices.put_mapping(index=self.index_name, doc_type=self.doc_type, body=self.mapping)
        print("created index:" + self.index_name)

    def xml2json(self, xmlpath):
        # 将xml数据转化为dict
        with open(xmlpath, "r") as xmlf:
            xml_str = xmlf.read()
            dict_str = xmltodict.parse(xml_str)
            # json_str = json.dumps(dict_str)
            return dict_str

    def cleanData(self, doc):
        raw_tokens = self.tokenizer.tokenize(doc.lower())
        lem_tokens = [self.stemmer.stem(token) for token in raw_tokens]
        lem_tokens = [
            token for token in lem_tokens if not token.isdigit() and len(token) > 1
        ]
        lem_tokens_without_stopword = filter(
            lambda i: i not in self.stopwords, lem_tokens
        )
        return " ".join(list(lem_tokens_without_stopword))

    def clean(self, json_data):
        if json_data["brief_title"]:
            json_data["brief_title"] = self.cleanData(json_data["brief_title"])
        if json_data["official_title"]:
            json_data["official_title"] = self.cleanData(json_data["official_title"])
        if json_data["brief_summary"]:
            json_data["brief_summary"] = self.cleanData(json_data["brief_summary"])
        if json_data["detailed_description"]:
            json_data["detailed_description"] = self.cleanData(
                json_data["detailed_description"]
            )
        if json_data["eligibility"]["criteria"]["textblock"]:
            json_data["eligibility"]["criteria"]["textblock"] = self.cleanData(
                json_data["eligibility"]["criteria"]["textblock"]
            )
        return json_data

    def oswalk(self):
        count = 0

        # 遍历xml_path中所有文件夹下的所有文件
        for os_set in os.walk(self.xml_path, topdown=True):
            for filename in os_set[2]:
                try:
                    filepath = os.path.join(os_set[0], filename)
                    json_data = self.xml2json(filepath)

                    cleaned_json_data = {}

                    default_input_json = {
                        "id_info": "NCT00000000",
                        "brief_title": "",
                        "official_title": "",
                        "brief_summary": "",
                        "detailed_description": "",
                        "intervention": {"intervention_type": "", "intervention_name": ""},
                        "eligibility": {
                            "criteria": {"textblock": ""},
                            "gender": "All",
                            "minimum_age": "6 Months",
                            "maximum_age": "100 Years",
                            "healthy_volunteers": "No",
                        },
                        "keyword": [],
                        "intervention_browse": [],
                        "condition": [],
                    }

                    # 将important.txt中设定好的字段从dict中提取出来，填充到要存进es的dict中
                    for field in self.fields:
                        if field in json_data["clinical_study"]:
                            if len(self.fields[field]) > 1 and not isinstance(
                                json_data["clinical_study"][field], str
                            ):
                                cleaned_json_data[field] = json_data["clinical_study"][
                                    field
                                ][self.fields[field]]
                            else:
                                cleaned_json_data[field] = json_data["clinical_study"][
                                    field
                                ]
                        else:
                            cleaned_json_data[field] = default_input_json[field]
                            # if len(self.fields[field]) > 1 and not isinstance(
                            #     default_input_json[field], str
                            # ):
                            #     cleaned_json_data[field] = default_input_json[field][
                            #         self.fields[field]
                            #     ]
                            # else:
                            #     cleaned_json_data[field] = default_input_json[field]

                    # 处理年龄
                    # print(default_input_json)
                    # print(cleaned_json_data)
                    if "eligibility" in cleaned_json_data:
                        if "criteria" not in cleaned_json_data["eligibility"]:
                            cleaned_json_data["eligibility"]["criteria"] = {"textblock": ""}

                        for k in default_input_json["eligibility"]:
                            if k not in cleaned_json_data["eligibility"]:
                                cleaned_json_data["eligibility"][k] = default_input_json["eligibility"][k]

                        cleaned_json_data["eligibility"] = NormalAge(
                            cleaned_json_data["eligibility"]
                        )

                    cleaned_json_data = self.clean(cleaned_json_data)

                    # ----------------------------------
                    # print(cleaned_json_data)
                    # return
                    # ----------------------------------

                    # 插入数据
                    self.es.index(
                        index=self.index_name,
                        body=cleaned_json_data,
                        doc_type=self.doc_type,
                    )

                    count += 1
                    if count % 1000 == 0:
                        print("Already finished:" + str(count))
                except KeyboardInterrupt:
                    # 处理ctrl+C中断程序的情况
                    print("Interrupted")
                    try:
                        sys.exit(0)
                    except SystemExit:
                        os._exit(0)
                except Exception as e:
                    print(cleaned_json_data)
                    print(e)
                    with open("errorxml.txt", "a") as f:
                        f.write(str(filepath) + "\n")
                    print("Error in ", str(filename))


if __name__ == "__main__":
    DP = DataPreprocessing()
    DP.oswalk()
