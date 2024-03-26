"""
Faceted Bullet Chart
--------------------
This example shows how to facet and layer bar charts to create a bullet chart.
"""
# category: other charts
import altair as alt

source = {'values': [
    {'title': 'Revenue', 'subtitle': 'US$, in thousands',
     'ranges': [150, 225, 300], 'measures': [220, 270], 'markers': [250]
     },
    {'title': 'Profit', 'subtitle': '%',
     'ranges': [20, 25, 30], 'measures': [21, 23], 'markers': [26]
     },
    {'title': 'Order Size', 'subtitle': 'US$, average',
     'ranges': [350, 500, 600], 'measures': [100, 320], 'markers': [550]
     },
    {'title': 'New Customers', 'subtitle': 'count',
     'ranges': [1400, 2000, 2500], 'measures': [1000, 1650], 'markers': [2100]
     },
    {'title': 'Satisfaction', 'subtitle': 'out of 5',
     'ranges': [3.5, 4.25, 5], 'measures': [3.2, 4.7], 'markers': [4.4]
     }
]}

base = alt.Chart(source)

chart = base.mark_bar(
).encode(
    x=alt.X('ranges[2]:Q', scale=alt.Scale(nice=False)),
    color=alt.value('#eee')
)

chart += base.mark_bar(
).encode(
    x='ranges[1]:Q',
    color=alt.value('#ddd')
)

chart += base.mark_bar(
).encode(
    x='ranges[0]:Q',
    color=alt.value('#ccc')
)

chart += base.mark_bar(
).encode(
    x='measures[1]:Q',
    color=alt.value('lightsteelblue'),
    size=alt.value(10),
    opacity=alt.value(1)
)

chart += base.mark_bar(
).encode(
    x='measures[0]:Q',
    color=alt.value('steelblue'),
    size=alt.value(10)
)

chart += base.mark_tick(
).encode(
    x='markers[0]:Q',
    color=alt.value('black')
)

chart.facet(
    row=alt.Row('title:N', title=None,
                header=alt.Header(labelAngle=0, labelAlign='left', title=None))
).resolve_scale(
    x='independent'
).configure_facet(
    spacing=10
).configure_axis(
    title=None
).configure_tick(
    thickness=2
)
