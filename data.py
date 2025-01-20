import pandas as pd
import yfinance as yf
import backtrader as bt
from backtrader.analyzers import Returns

if __name__ == '__main__':
    # 1. 获取历史数据
    data = yf.download('AAPL', start='2020-01-01', end='2023-01-01')

    # 2. 数据预处理
    data = data.ffill().bfill()

    # 3. 计算移动平均线
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    data['SMA200'] = data['Close'].rolling(window=200).mean()

    # 4. 创建交易信号
    data['Position'] = 0
    data.loc[data['SMA50'] > data['SMA200'], 'Position'] = 1
    data.loc[data['SMA50'] < data['SMA200'], 'Position'] = -1

    # 5. 去除缺失值
    data = data.dropna()
    print(data.index)

    # 6. 定义策略类
    class SMACrossStrategy(bt.Strategy):
        params = (
            ('sma_period1', 50),
            ('sma_period2', 200),
        )

        def __init__(self):
            self.sma1 = bt.indicators.SimpleMovingAverage(
                self.data.close, period=self.params.sma_period1)
            self.sma2 = bt.indicators.SimpleMovingAverage(
                self.data.close, period=self.params.sma_period2)
            self.crossover = bt.indicators.CrossOver(self.sma1, self.sma2)

        def next(self):
            if not self.position:
                if self.crossover > 0:
                    self.buy()
            elif self.crossover < 0:
                self.sell()

    # 7. 设置回测引擎
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SMACrossStrategy)
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)
    cerebro.addanalyzer(Returns, _name='returns')
    cerebro.broker.setcash(100000.0)

    # 8. 运行回测并输出结果
    results = cerebro.run()
    strategy = results[0]
    print('Initial Portfolio Value: %.2f' % cerebro.broker.startingcash)
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print('Returns:', strategy.analyzers.returns.get_analysis())

    # 9. 绘制结果
    cerebro.plot()
