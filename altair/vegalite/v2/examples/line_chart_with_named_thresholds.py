"""
Line Chart with Named Thresholds
-------------------
How to draw thresholds in the chart with a descriptive name.
"""
# category: line charts
import altair as alt
import pandas as pd

# Games data
data = [
    ['2015-04-01', 'Real Madrid', 0],
    ['2015-04-08', 'Real Madrid', 3],
    ['2015-04-15', 'Real Madrid', 1],
    ['2015-04-22', 'Real Madrid', 3],
    ['2015-04-29', 'Real Madrid', 0],
    ['2015-05-05', 'Real Madrid', 0],
    ['2015-05-12', 'Real Madrid', 0],
    ['2015-05-19', 'Real Madrid', 0],
    ['2015-04-26', 'Real Madrid', 1],
    ['2015-06-03', 'Real Madrid', 3],
    ['2015-04-01', 'Barcelona', 3],
    ['2015-04-08', 'Barcelona', 0],
    ['2015-04-15', 'Barcelona', 3],
    ['2015-04-22', 'Barcelona', 3],
    ['2015-04-29', 'Barcelona', 3],
    ['2015-05-05', 'Barcelona', 0],
    ['2015-05-12', 'Barcelona', 3],
    ['2015-05-19', 'Barcelona', 1],
    ['2015-05-26', 'Barcelona', 3],
    ['2015-06-03', 'Barcelona', 3],
]
data = pd.DataFrame(data, columns=['date', 'Team', 'points'])

# The basic line chart
line = alt.Chart().mark_line().encode(
    x=alt.X('date:T', title='Games'),
    y=alt.Y('points:Q', title='Points', 
            scale=alt.Scale(domain=[-1, 4])),
    color='Team:N'
)

thresholds_data = pd.DataFrame([
    {"th_value": 3, "th": "victory"},
    {"th_value": 1, "th": "tie"},
    {"th_value": 0, "th": "defeat"},
])
thresholds_rules = alt.Chart(thresholds_data).mark_rule().encode(
    y='th_value:Q', 
    opacity=alt.value(0.3)
)
thresholds_text = alt.Chart(thresholds_data).mark_text(
    align='left', dx=-290, dy=-5
).encode(
    alt.Y('th_value:Q'),
    text='th',
)
thresholds = thresholds_rules + thresholds_text

alt.layer(line, thresholds, data=data, width=600, height=300).configure_axisY(labels=False)
