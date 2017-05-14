# -*-coding:utf-8-*-
# designed by Ziyu Jiang
# 文件中的函数涉及数据清洗、文本挖掘等

import importlib, sys
importlib.reload(sys)
sys.path.append('/Users/admin/anaconda/lib/python3.6/site-packages')
import re
import pymysql
import pandas as pd
import snownlp
from snownlp import sentiment
from snownlp import SnowNLP

# 连接本地数据库(需要输入用户名、密码)
conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='anTHEM1102',db='News', charset = 'utf8')

# 从URL中获取网址并将关键信息存入数据库
def getContent(line):

    # s = 0
    # 和讯网采用MongoDB存储，可提取统一格式并存放到items中
    pattern = re.compile('"entitytime":".*?"},', re.S)
    items = re.findall(pattern, line)

    for item in items:
        # 激活数据库指针
        cur = conn.cursor()
        # s += 1
        # print(s)
        # print(item)
        # 按照一定的格式
        time = item[14:25]
        print(time)
        newsid = item[94:103]
        title = item[113:-3]
        # 插入拼接URL
        # 此处的网址与年份有关
        url = 'http://gold.hexun.com/' + '2017-' + str(time[0:2]) + '-' + str(time[3:5]) + '/' + newsid + '.html'
        print(url)
        # 修改为统一的DATETIME格式
        time = '2017-' + str(time[0:2]) + '-' + str(time[3:5]) + ' ' + str(time[6:8]) + ':' + str(time[9:11])
        # file.writelines(item+'\n')
        # print(time)
        # print(title)
        # 计算得分
        score = SnowNLP(title).sentiments
        sql = "insert into NEWS (TITLE, NEWSTIME, NEWSID, url, SCORE) values ('" + title.encode('utf-8').decode('utf-8') + "','" + time + "','"+newsid + "','" + url + "','" + str(score) + "')"
        # print(sql)
        # 异常处理
        try:
            cur.execute(sql)
        except Exception as e:
            conn.commit()
            cur.close()

# 利用SnowNLP计算一段时间内新闻的情感因子的平均值
def calculateProb(start, end, lgreturn):
    # 全局变量；用于校正没有新闻的时间的影响
    global oldscore
    cur = conn.cursor()

    sql = "select ID, TITLE from NEWS where NEWSTIME between '" + start + "' and '" + end + "'"
    # print(sql)
    cur.execute(sql)
    res = cur.fetchall()
    l = len(res)
    sumscore = 0
    for i in range(0,l):
        entry = res[i]
        title = entry[1]
        id = entry[0]
        sumscore += SnowNLP(title).sentiments
    lgreturn = str(round(lgreturn,4))
    # 计算情感因子的平均值
    if l != 0:
        score = str(round(sumscore / l, 4))
    else:
    # 对于没有新闻的时段，按照前一时刻的平均值*0.9进行修正
        score = str(round(float(oldscore)*0.9, 4))
    # 结果存入数据库
    sql = "INSERT INTO hourly (starttime, endtime, logreturn, score) VALUES " + "('" + str(start) + "','" + str(end) \
          + "','" + lgreturn + "','" + score +"')"
    print(sql)
    cur.execute(sql)
    conn.commit()
    return score



# 计算每天的得分情况，在用日线研究时曾使用
def insertscore(startmonth):
    cur = conn.cursor()
    for month in range(startmonth, 13):
        for day in range(1, 32):
            if len(str(day)) < 2:
                d = '0' + str(day)
            else:
                d = str(day)
            if len(str(day + 1)) < 2:
                dplus = '0' + str(day + 1)
            else:
                dplus = str(day + 1)
            if len(str(month)) < 2:
                m = '0' + str(month)
            else:
                m = str(month)
            date = '2016-' + m + '-' + d + ' 00:00'
            nextdate = '2016-' + m + '-' + dplus + ' 00:00'
            conn.commit()
            try:
                sql = "insert into date (date, score) values ('" + str(date) + "','" + str(
                    dailyaverage(date, nextdate)) + "')"
                print(sql)

                cur.execute(sql)

                conn.commit()
            except:
                print("index out of bonds")

# 计算日内得分均值（日线用）
def dailyaverage(day, dayplus):

    cur = conn.cursor()
    sql = "select ID, TITLE, SCORE from NEWS where NEWSTIME between '" + day + "' and '" + dayplus + "'"
    print(sql)
    cur.execute(sql)
    res = cur.fetchall()
    l = len(res)
    sum = 0
    print(res)
    for i in range(0, l):
        entry = res[i]
        sum += entry[2]
    print(sum/l)
    conn.commit()
    return sum/l


if __name__ == '__main__':

    data read-in
    df = pd.read_excel('/Users/admin/Desktop/quant/gold.xlsx')
    length_file = len(df)

    # calculate factor of public sentiment
    for i in range(1, length_file):
        # the start time and end time for each calculation of sentiment factor
        time_new = str(df.values[i, 0])
        time_old = str(df.values[i-1, 0])
        logreturn = df.values[i, 2]

        # oldscore = calculateProb(time_old, time_new, logreturn)



    #  calculateProb('2015-01-01 00:00', '2016-12-31 00:00')
    #  insertscore(1)
    # for line in open('/Users/admin/Desktop/quant/news01.txt'):
        # getContent(line)


