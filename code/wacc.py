"""Estimate the client's WACC.

Run from the repo root:   python code/wacc.py
Reads:  inputs/assumptions.csv
Writes: outputs/wacc.csv (one row; the columns are listed in README.md)

Owner: the developer. Fill in the three TODO functions (your agent can help),
then run it and check the numbers make sense before you open a pull request.
"""
import pandas as pd
import yfinance as yf

CLIENT = 'PENG'  # Penguin Solutions, named in README.md
MKT = 'SPY'
YEARS = 5


def get_returns(ticker, mkt=MKT, years=YEARS):
    """Daily returns for the client and the market over the last `years` years.
    Returns a DataFrame with two columns, named ticker and mkt, and no missing values."""
    # threads=False: with threads on, yfinance's sqlite cache raised 'database is locked'
    # and SPY silently came back all NaN
    px = yf.download([ticker, mkt], period=f'{years}y', auto_adjust=True,
                     progress=False, threads=False)['Close']
    px = px[[ticker, mkt]]
    assert px.notna().any().all(), f'no prices for: {list(px.columns[px.isna().all()])}'
    rets = px.pct_change().dropna()
    # dropna should only lose the first row; losing more means gaps or a short history
    assert len(rets) > 0.95 * (len(px) - 1), \
        f'only {len(rets)} of {len(px) - 1} days have returns for both {ticker} and {mkt}'
    return rets


def estimate_beta(rets, ticker, mkt=MKT):
    """Equity beta: cov(stock, market) / var(market)."""
    return float(rets[ticker].cov(rets[mkt]) / rets[mkt].var())


def compute_wacc(beta, a):
    """a is a dict of assumptions: rf, mrp, rd, tax, w_e, w_d.
    Returns a dict with cost_of_equity and wacc (and the inputs), matching the README's columns."""
    cost_of_equity = a['rf'] + beta * a['mrp']
    wacc = a['w_e'] * cost_of_equity + a['w_d'] * a['rd'] * (1 - a['tax'])
    return {'rf': float(a['rf']), 'mrp': float(a['mrp']), 'cost_of_equity': float(cost_of_equity),
            'rd': float(a['rd']), 'tax': float(a['tax']), 'w_e': float(a['w_e']),
            'w_d': float(a['w_d']), 'wacc': float(wacc)}


if __name__ == '__main__':
    a = pd.read_csv('inputs/assumptions.csv', index_col='item')['value'].to_dict()
    assert abs(a['w_e'] + a['w_d'] - 1) < 1e-6, 'weights must sum to 1'

    rets = get_returns(CLIENT)
    assert len(rets) > 1000, 'expected about 5 years of daily returns'

    beta = estimate_beta(rets, CLIENT)
    out = compute_wacc(beta, a)
    out = {'ticker': CLIENT, 'asof': rets.index.max().date(), 'beta': beta, **out}

    assert 0 < out['wacc'] < 0.25, 'WACC outside 0-25%: check the inputs'
    cols = ['ticker', 'asof', 'beta', 'rf', 'mrp', 'cost_of_equity', 'rd', 'tax', 'w_e', 'w_d', 'wacc']
    pd.DataFrame([out])[cols].to_csv('outputs/wacc.csv', index=False)
    print(pd.DataFrame([out])[cols].T)
