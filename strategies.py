from collections import defaultdict
from dateutil import parser
from functools import reduce
from iex_utils import create_df_from_symbols

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


compound = lambda x: (1 + x).prod() - 1
daily_sr = lambda x: x.mean() / x.std()


def heatmap(df, cmap=plt.cm.gray_r):

    fig = plt.figure()
    ax = fig.add_subplot(111)
    axim = ax.imshow(df.values, cmap=cmap, interpolation='nearest')
    ax.set_xlabel(df.columns.name)
    ax.set_xticks(np.arange(len(df.columns)))
    ax.set_xticklabels(list(df.columns))
    ax.set_ylabel(df.index.name)
    ax.set_yticks(np.arange(len(df.index)))
    ax.set_yticklabels(list(df.index))
    plt.colorbar(axim)
    plt.show()


def get_portfolio_logic(price, lookback, lag):

    momentum = price.shift(lag).pct_change(lookback)
    ranks = momentum.rank(axis=1, ascending=False)
    best_ten = lambda x: list(map(lambda y: y
                                  if y > price.shape[1] - 10
                                  else 0, x))
    ranks = ranks.apply(best_ten, axis=1)
    return ranks


def some_strategy(prices, lb, hold):

    # Compute portfolio weights
    freq = '%dB' % hold
    port = get_portfolio_logic(prices, lb, lag=0)

    daily_rets = prices.pct_change()

    port = port.shift(1).resample(freq).first() # shift 1 for trading at the close
    returns = daily_rets.resample(freq).apply(compound)
    port_rets = (port * returns).sum(axis=1)

    return daily_sr(port_rets) * np.sqrt(252 / hold)


def test_some_strategy(prices, given_strategy, sector_name):

    lookbacks = range(30, 120, 10)
    holdings = range(30, 120, 10)
    dd = defaultdict(dict)

    for lb in lookbacks:
        for hold in holdings:
            dd[lb][hold] = given_strategy(prices, lb, hold)

    ddf = pd.DataFrame(dd)
    ddf.index.name = 'Holding Period'
    ddf.columns.name = 'Lookback Period'
    # heatmap(ddf)
    ddf.to_csv('./iexdata/{}_top_10_long_only_sharp_ratios'.format(sector_name))


def example():
    spx_table = pd.read_csv('./iexdata/10K_data.csv')
    sectors_list = list(set(spx_table['Sector']))
    by_sectors = spx_table.groupby('Sector')

    for s in sectors_list:
        sector_tickers = by_sectors.get_group(s)['Symbol']
        temp_df = create_df_from_symbols(*sector_tickers)
        columns_to_drop = list(filter(lambda x: 'close' not in x, temp_df.columns))
        temp_df.drop(columns_to_drop, axis=1, inplace=True)
        test_some_strategy(temp_df, some_strategy, s)


if __name__ == '__main__':
    example()

