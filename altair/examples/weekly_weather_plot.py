"""
Weekly Weather Plot
-------------------
Inspired by this `Vega-Lite example <https://vega.github.io/vega-lite/examples/bar_layered_weather.html>`_ by `@melissatdiamond <https://github.com/melissatdiamond>`_. This example shows how to layer bar charts to plot weekly weather data.
"""
# category: case studies
import altair as alt
from vega_datasets import data

source = data.weather()

base = alt.Chart(source).encode(
    x=alt.X('id:O',
            axis=alt.Axis(
                domain=False,
                ticks=False,
                labels=False,
                title=None,
                titlePadding=25,
                orient='top'
            )
            ),
)

chart = base.mark_bar(
    style='box'
).encode(
    y=alt.Y('record.low:Q',
            scale=alt.Scale(domain=[10, 70]),
            axis=alt.Axis(title='Temperature (F)')
            ),
    y2='record.high:Q',
    size=alt.value(20),
    color=alt.value('#ccc')
)

chart += base.mark_bar(
    style='box'
).encode(
    y='normal.low:Q',
    y2='normal.high:Q',
    size=alt.value(20),
    color=alt.value('#999')
)

chart += base.mark_bar(
    style='box'
).encode(
    y='actual.low:Q',
    y2='actual.high:Q',
    size=alt.value(12),
    color=alt.value('#000')
)

chart += base.mark_bar(
    style='box'
).encode(
    y='forecast.low.low:Q',
    y2='forecast.low.high:Q',
    size=alt.value(12),
    color=alt.value('#000')
)

chart += base.mark_bar(
    style='box'
).encode(
    y='forecast.low.high:Q',
    y2='forecast.high.high:Q',
    size=alt.value(3),
    color=alt.value('#000')
)

chart += base.mark_bar(
    style='box'
).encode(
    y='forecast.high.low:Q',
    y2='forecast.high.high:Q',
    size=alt.value(12),
    color=alt.value('#000')
)

chart += base.mark_text(
    align='center',
    baseline='bottom',
).encode(
    text='day:N',
    y=alt.value(-5)
)

chart.properties(
    title=['Weekly Weather', 'Observations and Predictions'],
    width=250,
    height=200
).configure_title(
    frame='group'
)
