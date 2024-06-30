"""
Bar Chart with Highlighted Segment
----------------------------------
This example shows a bar chart that highlights values beyond two threshold.
"""
# category: bar charts
import altair as alt
import pandas as pd
from vega_datasets import data

source = data.wheat()
threshold = pd.DataFrame(
    data={"threshold_value": [20, 60], "threshold_label": ["> 20", "> 60"]}
    )

bars = alt.Chart(source).mark_bar(color="#9CC8E2").encode(
    x="year:O",
    y=alt.Y("wheat:Q",title="Wheat")
)

highlight = alt.Chart(source).mark_bar(color="#5BA3CF").encode(
    x='year:O',
    y='wheat:Q',
    y2=alt.datum(20)
).transform_filter(
    alt.datum.wheat > 20
)

highlight2 = alt.Chart(source).mark_bar(color="#2978B8").encode(
    x='year:O',
    y='wheat:Q',
    y2=alt.datum(60)
).transform_filter(
    alt.datum.wheat > 60
)

rule = alt.Chart(threshold).mark_rule().encode(
    y=alt.Y("threshold_value")
)

label = rule.mark_text(
    x=alt.expr('width'), align="right",dx=20, dy=-5, fontWeight="bold", fontSize=12
).encode(
    text="threshold_label",
)

(bars + highlight + highlight2 + rule +label).properties(width=600)