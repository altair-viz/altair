"""
Cyberpunk Style Plot
--------------------
Inspired by `this chart <https://towardsdatascience.com/cyberpunk-style-with-matplotlib-f47404c9d4c5>`_ by `@d_haitz <https://twitter.com/d_haitz>`_. This example shows how to layer line plots of varying size to create a neon glow effect.
"""
# category: case studies
import altair as alt
import pandas as pd

df = pd.DataFrame({'A': [1, 3, 9, 5, 2, 1, 1],
                   'B': [4, 5, 5, 7, 9, 8, 6]})

base = alt.Chart(
    df.reset_index().melt(id_vars='index')
).encode(
    x=alt.X('index:Q'),
    y=alt.Y('value:Q'),
    color=alt.Color('variable:N',
                    scale=alt.Scale(range=['#08F7FE', '#FE53BB']))
)

# draw lines and circles
chart = base.mark_circle(size=100, opacity=1)
chart += base.mark_line(size=2.5)

# make it glow
n_lines = 10
diff_linewidth = 1.25
alpha_value = 0.3 / n_lines

for n in range(n_lines):
    line_width = 5 + (diff_linewidth * n)
    chart += base.mark_line(opacity=alpha_value,
                            size=line_width)

# fill area underneath lines
chart += base.mark_area(opacity=0.1)

chart.configure_axis(
    title=None,
    ticks=False,
    domain=False,
    gridColor='#2A3459',
    labelColor='#D3D3D3',
    labelFontSize=14,
    labelPadding=10,
    labelSeparation=40
).configure_legend(
    title=None,
    labelColor='#D3D3D3',
    labelFontSize=14,
    orient='top-right',
    symbolType='stroke',
    symbolStrokeWidth=3,
    symbolSize=600
).configure_view(
    strokeWidth=0
).properties(
    background='#212946',
    width=600,
    height=350
)
