import configparser
import json

class Conf(object):
    def __init__(self):
        self.conf = configparser.ConfigParser()

    def getConfig(self, section, key):
        # 读取ir.conf中的设定
        self.conf.read('ir.conf')
        return self.conf.get(section, key)

    def getMapping(self):
        # 读取elasticsearch的数据格式
        with open('mapping.json', 'r') as f:
            map_json = json.loads(f.read())
        return map_json

    def getSeachModel(self):
        with open('searchbody.json', 'r') as f:
            searchbody = json.loads(f.read())
        return searchbody

    def getImportant(self):
        # important.txt中是需要从原始数据中提取出来的字段
        dict_important = {}
        with open('important.txt', 'r') as f:
            for line in f.readlines():
                k, v = line.strip().split(':')
                dict_important[k] = v
        return dict_important

    def getGenFields(self):
        with open('ir.txt', 'r') as f:
            fields_data = f.read()
            return(fields_data.split('#'))
