## 文件说明

models 保存训练好的模型

ir.conf 设置文件目录，ES的index等，注意不需要加引号

important.txt 需要提取出来的字段，格式为[字段名]:[字段下需要提取的数据]，引号后可以为空

ir.txt gensim训练模型所需字段，用#分割


Config.py 读取项目设置

DataProcessing.py 数据预处理

Query.py  查询 

utils.py 工具函数


## 使用方法：

1.修改ir.conf中的文件路径、index名称、doc_type

2.python DataProcessing.py ：将数据存进ElasticSearch

3.python Query.py : 查询

python版本：3.6

## pip:

configparser

xmltodict

elasticsearch

elasticsearch_dsl

pyes

nltk

gensim

# 注意：
需要先安装elasticsearch服务器并启动

目前查询功能和文档打分功能尚有问题，会尽快修复完善

gensim训练数据量过于庞大，需要想办法优化
