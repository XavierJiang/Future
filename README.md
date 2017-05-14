# Future
---
title: "R Notebook"
output:
  html_document: default
  html_notebook: default
  pdf_document: default
---

## 读入数据

```{r}
setwd("/Users/admin/Desktop/Time Series")
test <- read.csv("w.csv",header = T)
plot.ts(test$logreturn)
plot.ts(test$score)
```


```{r}
acf(test$logreturn)
pacf(test$logreturn)
```

ACF与PACF函数均没有明显的特征。因此，我们比较几种可能情况下的指标确定均值方程。

## 单位根与趋势项检验
```{r}
library(tseries)
library(forecast)
adf.test(test$logreturn)
# 判断差分阶数
ndiffs(test$logreturn)
```
p<0.01, 因此我们可以拒绝有趋势项的原假设。

## 参数估计

几种ARIMA模型的AIC，BIC，似然函数基本一致，考虑到AR(1)模型的AIC相对较大，且与二阶自回归相比参数显著，考虑选用AR（1）模型拟合均值方程。
```{r}
library(TSA)
arima(test$logreturn, order=c(1,0,0))
arima(test$logreturn, order=c(2,0,0))
arima(test$logreturn, order=c(0,0,1))
arima(test$logreturn, order=c(0,0,2))
arima(test$logreturn, order=c(1,0,1))
```

## 残差检验
### 残差图
```{r}
model_1 <- arima(test$logreturn, c(1,0,0))
# 模型残差
res_1 <- rstandard(model_1)
plot.ts(res_1)
plot.ts(res_1^2)
```
可以观察到残差仍然符合“波动率聚类”现象，即剧烈的波动附近有较大几率出现较大波动。

### 残差的自相关与方差齐性检验
```{r}
#检验残差自相关性
Box.test(res_1, lag = 1,type = "Ljung-Box")
#检验残差方差齐性
ML_test <- McLeod.Li.test(model_1)
```
Box-Ljung 检验结果显示p值大于0.05，无法拒绝残差没有相关性的假设；
Mcleod-Li 检验中各阶p值均小于0.05，拒绝方差齐次的假定，表明序列中存在ARCH效应


## 建立GARCH模型(不考虑舆情因子)
由于GARCH模型的定阶较为复杂，选择使用GARCH(1,1)拟合序列。
```{r}
# 确定测试集和训练集
l <- length(test$logreturn)-42
trainset <- test$logreturn[1:l]
testset <- test$logreturn[l:length(test$logreturn)]

# 重新调整后的GARCH模型
myspec <- ugarchspec(variance.model =  list(model = "fGARCH", garchOrder = c(1, 1),submodel = "GARCH", external.regressors = NULL, variance.targeting = FALSE), mean.model = list(armaOrder = c(1, 0), include.mean = TRUE, archm = FALSE, archpow = 1, arfima = FALSE, external.regressors = NULL, archex = FALSE), distribution.model = "norm")

myfit=ugarchfit(myspec,data=trainset,solver="solnp")
myfit
```
观察到一阶自回归项不显著。
```{r}
# 重新调整后的GARCH模型
myspec <- ugarchspec(variance.model =  list(model = "fGARCH", garchOrder = c(1, 1),submodel = "GARCH", external.regressors = NULL, variance.targeting = FALSE), mean.model = list(armaOrder = c(0, 0), include.mean = TRUE, archm = FALSE, archpow = 1, arfima = FALSE, external.regressors = NULL, archex = FALSE), distribution.model = "norm")

myfit=ugarchfit(myspec,data=trainset,solver="solnp")
myfit
```

从结果中可以看出，在GARCH模型中，一阶自回归系数不显著，这可能是由于模型中的外生变量不足，无法有效地从历史数据中得到足够的信息；另一方面，经典GARCH模型的作用主要在于解释波动率而不是均值。

```{r}
resid <- residuals(myfit)
acf(resid, xlim = c())
pacf(resid, xlim = c())
```
模型拟合的残差基本符合非自相关、方差齐次等假定。
```{r}
forc = ugarchforecast(myfit, n.ahead = 40)

# 预测值和真实值
plot.ts(testset, main = "fitted mean versus real")
lines(fitted(forc))

# 波动率预测
plot.ts(sigma(forc), main = "fitted sigma versus real")
```
由于我们使用的均值模型为ARIMA(0，0，0),所以预报结果显示均价为一条直线；实际上预测值基本围绕这一水平波动。
而波动率有一个上升的预测，而实际上序列的波动率保持不变，甚至稍有减少。

## 建立GARCH模型(考虑舆情因子)
将新闻的舆情因子作为外生变量，加入到模型的波动率方程中，有如下结果。
```{r}
myspec <- ugarchspec(variance.model =  list(model = "fGARCH", garchOrder = c(1, 1),submodel = "GARCH", external.regressors = as.matrix(test$score), variance.targeting = FALSE), mean.model = list(armaOrder = c(0, 0), include.mean = TRUE, archm = FALSE, archpow = 1, arfima = FALSE, external.regressors = NULL, archex = FALSE), distribution.model = "norm")

myfit2=ugarchfit(myspec,data=trainset,solver="solnp")
myfit2
```

残差较之前相比有更良好的性质，说明模型拟合效果较好。
```{r}
resid <- residuals(myfit)
acf(resid, xlim = c())
pacf(resid, xlim = c())
```

```{r}
forc2 = ugarchforecast(myfit2, n.ahead = 40)

# 预测值和真实值
plot.ts(testset, main = "fitted mean versus real")
lines(fitted(forc2))

# 波动率预测
plot.ts(sigma(forc2), main = "fitted sigma versus real")
```
可以观察到，本模型中均值仍然保持不变，而波动率有下降的趋势，较为符合实际情况。

###TGARCH模型
考虑到正负残差对于下一时刻的波动率有非对称的影响，考虑采用非对称GARCH模型进行建模。在本模型下，AR（1）项在90%置信水平意义下显著，纳入模型中。波动率方程中alpha项不显著，故删去。

该模型下的四个参数都对结构有显著的影响。
```{r}
myspec <- ugarchspec(variance.model =  list(model = "fGARCH", garchOrder = c(1, 1),submodel = "TGARCH", external.regressors = NULL, variance.targeting = FALSE), mean.model = list(armaOrder = c(1, 0), include.mean = TRUE, archm = FALSE, archpow = 1, arfima = FALSE, external.regressors = NULL, archex = FALSE), distribution.model = "norm")

myfit3=ugarchfit(myspec,data=trainset,solver="solnp")
myfit3
```


预测结果显示均值缓慢上升，而未来短期内的波动率迅速上升，说明这可能不是一个稳定的预判。
```{r}
forc3 = ugarchforecast(myfit3, n.ahead = 40)

# 预测值和真实值
plot.ts(testset, main = "fitted mean versus real")
lines(fitted(forc3))

# 波动率预测
plot.ts(sigma(forc3), main = "fitted sigma versus real")
```


### GARCH-M 模型
如下所示的GARCH-IN-MEAN模型中，将舆情因子作为均值方差中的外生变量。
```{r}
myspec <- ugarchspec(variance.model =  list(model = "fGARCH", garchOrder = c(0, 1),submodel = "GARCH", external.regressors = NULL, variance.targeting = FALSE), mean.model = list(armaOrder = c(0, 0), include.mean = TRUE, archm = TRUE, archpow = 1, arfima = FALSE, external.regressors = as.matrix(test$score), archex = FALSE), distribution.model = "norm")

myfit4=ugarchfit(myspec,data=trainset,solver="solnp")
myfit4
```
```{r}
forc = ugarchforecast(myfit4, n.ahead = 40)

# 预测值和真实值
plot.ts(testset, main = "fitted mean versus real")
lines(fitted(forc))

# 波动率预测
plot.ts(sigma(forc), main = "fitted sigma")
```
模型的预测结果显示，未来五天内的价格有继续上升的趋势，且波动率在逐渐下降，和测试集的实际情况较为符合。

通过上面的描述，在考虑了舆情因子的模型中，T-GARCH模型和GARCH-M模型都有比较良好的性能，且各有优劣：T-GARCH模型关于波动率的方差有效性稍差，而GARCH-M的信号偏误检验有一项没有通过（这可能说明波动率收到其他已知变量的影响，违反了假设）

## 模型预测

注意：截止周日上日8点本接口最新的分时数据记录到2017-05-13 01:30:00， 故往后5天的预测均以此为准！

故将原有的测试集加入到总训练集中，并采用Garch-in-mean模型进行预报：
```{r}
myspec <- ugarchspec(variance.model =  list(model = "fGARCH", garchOrder = c(0, 1),submodel = "GARCH", external.regressors = NULL, variance.targeting = FALSE), mean.model = list(armaOrder = c(0, 0), include.mean = TRUE, archm = TRUE, archpow = 1, arfima = FALSE, external.regressors = as.matrix(test$score), archex = FALSE), distribution.model = "norm")

myfit4=ugarchfit(myspec,data=test$logreturn,solver="solnp")
myfit4
```
```{r}
forc = ugarchforecast(myfit4, n.ahead = 40)

# 预测值和真实值
plot.ts(fitted(forc), main = "forecast mean")


# 波动率预测
plot.ts(sigma(forc), main = "forecast sigma")
```
因此未来数日预期黄金期货的均价会上升，且波动率预期下降，有利于投资。
