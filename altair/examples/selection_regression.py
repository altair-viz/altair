"""

## Linear Regression on Selected Samples:
=================
Reference `<https://github.com/Philliec459/Regression-Line-from-Points-Selected-off-of-Cross-Plot-using-Altair>`_. 
This example shows the regression line on selected samples. Samples are selected from the left chart, and one the right chart,
selected samples and the regression line are shown.
"""

import pandas as pd
import altair as alt

from math import floor, ceil
from vega_datasets import data

brush = alt.selection(type='interval')

source = data.iris()

chart_select_from = alt.Chart(source).mark_point(filled=True, size=100).encode(
    x=alt.X('sepalLength', scale = alt.Scale(zero = False)),
    y= alt.Y('petalLength', scale = alt.Scale(zero = False)),
    color=alt.condition(brush, 'species:N', alt.value('lightgray'))
).add_selection(
    brush
)

xmin = floor(source['sepalLength'].min())
xmax = ceil(source['sepalLength'].max())
ymin = floor(source['petalLength'].min())
ymax = ceil(source['petalLength'].max())
chart_select_to = alt.Chart(source).mark_point().encode(
    x=alt.X('sepalLength', scale = alt.Scale(domain= [xmin, xmax])),
    y= alt.Y('petalLength', scale = alt.Scale(domain= [ymin, ymax])),
    color='species'
).transform_filter(
    brush
)


Reg_Line = chart_select_to.transform_regression('sepalLength', 'petalLength',
                                      method="linear",
                                      groupby=["species"],
                                      extent = [xmin,xmax]
).mark_line()


chart_select_from + Reg_Line | chart_select_to + Reg_Line

