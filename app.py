"""The WACC card.

Run from the repo root:   streamlit run app.py

Owner: the product manager. This works today on the FAKE numbers, so you can build
the page before the real numbers exist. When the developer's pull request is merged,
outputs/wacc.csv appears and the app switches to it automatically.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

LABELS = {
    'rf': 'Risk-free rate',
    'mrp': 'Market risk premium',
    'rd': 'Pre-tax cost of debt',
    'tax': 'Tax rate',
    'w_e': 'Equity weight',
    'w_d': 'Debt weight',
}


def compute_wacc(beta, rf, mrp, rd, tax, w_d):
    """Same formulas as code/wacc.py; w_e is 1 - w_d. Returns (cost_of_equity, wacc)."""
    cost_of_equity = rf + beta * mrp
    return cost_of_equity, (1 - w_d) * cost_of_equity + w_d * rd * (1 - tax)


st.set_page_config(page_title='WACC card', layout='centered')

real = Path('outputs/wacc.csv')
card = pd.read_csv(real if real.exists() else 'outputs/wacc_FAKE.csv').iloc[0]
inputs = pd.read_csv('inputs/assumptions.csv', index_col='item')

if not real.exists():
    st.warning('Showing FAKE numbers. Run `python code/wacc.py` to make outputs/wacc.csv.')

st.title(f"WACC card: {card['ticker']}")
st.caption(f"Returns through {card['asof']}")

# The answer, in one sentence a CFO can act on
st.markdown(
    f"**{card['ticker']}'s WACC is {card['wacc']:.2%}.** A new project of average risk "
    f"should earn at least {card['wacc']:.2%} a year to create value for shareholders. "
    f"Riskier projects should clear a higher bar; safer ones can use a lower one."
)

c1, c2, c3 = st.columns(3)
c1.metric('WACC', f"{card['wacc']:.2%}")
c2.metric('Cost of equity', f"{card['cost_of_equity']:.2%}")
c3.metric('Beta', f"{card['beta']:.2f}")

st.subheader('What if?')
st.write('Move the sliders to see how the hurdle rate changes with leverage and the market risk premium.')

s1, s2 = st.columns(2)
w_d_pct = s1.slider(
    'Debt weight (w_d)', 0.0, max(80.0, card['w_d'] * 100),
    float(card['w_d'] * 100), 1.0, format='%.0f%%',
)
mrp_pct = s2.slider(
    'Market risk premium', min(3.0, card['mrp'] * 100), max(8.0, card['mrp'] * 100),
    float(card['mrp'] * 100), 0.25, format='%.2f%%',
)

new_ke, new_wacc = compute_wacc(
    card['beta'], card['rf'], mrp_pct / 100, card['rd'], card['tax'], w_d_pct / 100,
)
m1, m2 = st.columns(2)
m1.metric(
    'Scenario WACC', f'{new_wacc:.2%}',
    delta=f"{(new_wacc - card['wacc']) * 100:+.2f} pp", delta_color='inverse',
)
m2.metric(
    'Scenario cost of equity', f'{new_ke:.2%}',
    delta=f"{(new_ke - card['cost_of_equity']) * 100:+.2f} pp", delta_color='inverse',
)
st.caption(
    'Beta is held at its estimated value. In practice more debt also raises beta, '
    'so the true WACC falls less than shown as leverage rises.'
)

with st.expander('How the WACC is calculated'):
    st.latex(r'\text{Cost of equity} = r_f + \beta \times \text{MRP}')
    st.latex(r'\text{WACC} = w_e \times \text{Cost of equity} + w_d \times r_d \times (1 - t)')
    st.write(
        f"Beta is {card['ticker']}'s equity beta against SPY, from daily returns "
        f"over the last 5 years ending {card['asof']}."
    )

st.subheader('Inputs and sources')
table = pd.DataFrame({
    'Input': [LABELS.get(item, item) for item in inputs.index],
    'Value': inputs['value'].map('{:.2%}'.format).values,
    'Source': inputs['source'].values,
})
st.dataframe(table, hide_index=True, width='stretch')
