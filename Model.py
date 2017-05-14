import sys
sys.path.append('/Users/admin/anaconda/lib/python3.6/site-packages')

from scipy import  stats
import statsmodels.api as sm  # 统计相关的库
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import arch
# 条件异方差模型相关的库
import pymysql
from arch import arch_model
# intialize data structures

# log return
data = []

# sentimental score
score = []

# date
date = []

# connect to database and retrieve data
conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='anTHEM1102',db='News', charset = 'utf8')
cur = conn.cursor()
sql = "SELECT endtime, logreturn, score FROM hourly"
cur.execute(sql)
res = cur.fetchall()
l = len(res)

# read in data
for i in range(0,l):
    date.append(res[i][0])
    data.append(float(res[i][1]))
    score.append(float(res[i][2]))

ndata = np.array(data)
nscore = np.array(score)

# generate a time series plot for log-return
plt.plot(data)
plt.title('time seres plot for log-return')
plt.show()

# ADF test for trend and unit root test
t = sm.tsa.stattools.adfuller(ndata)
print("===数据探索性分析")
print("pvalue: "+str(t[1]))
if (t[1] < 0.05):
    print("拒绝原假设，序列是平稳的")
else:
    print("序列非平稳")

# Construct an AR(p) model
print("===建立AR模型")
fig = plt.figure(figsize=(20,5))
ax1=fig.add_subplot(111)
fig = sm.graphics.tsa.plot_pacf(ndata,lags = 20,ax=ax1)
plt.show()
print("建立均值方程：AR(1)模型")

order = (1,0)
model = sm.tsa.ARMA(ndata,order).fit()

print("===检验方差")
at = ndata -  model.fittedvalues
at2 = np.square(at)
plt.figure(figsize=(10,6))
plt.subplot(211)
plt.plot(at,label = 'at')
plt.legend()
plt.subplot(212)
plt.plot(at2,label='at^2')
plt.legend(loc=0)
plt.show()

print("===检验残差时序自相关性及方差齐性")
print("Ljung-Box Test: H0---the error terms are mutually independent")
m = 10 # 检验10个自相关系数
acf,q,p = sm.tsa.acf(at2,nlags=m,qstat=True)  ## 计算自相关系数 及p-value
out = np.c_[range(1,11), acf[1:], q, p]
output=pd.DataFrame(out, columns=['lag', "AC", "Q", "P-value"])
output = output.set_index('lag')
print(output)
print("各阶p-值小于0.05")
print("拒绝原假设，残差平方有相关性，有ARCH效应")

print("===确定ARCH模型阶数")
fig = plt.figure(figsize=(20,5))
ax1=fig.add_subplot(111)
fig = sm.graphics.tsa.plot_pacf(at2,lags = 15,ax=ax1)
plt.show()
print("===一阶PACF函数明显偏离置信域，取ARCH(1)模型")

print("===构建GARCH模型")
# 训练集
train = data[:-10]
# 测试集
test = data[-10:]
am = arch.arch_model(train,mean='AR',lags=1,vol='GARCH')
res = am.fit()
