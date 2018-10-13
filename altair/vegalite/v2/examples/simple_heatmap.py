"""
Simple Heatmap
--------------
This example shows a simple heatmap for showing gridded data.
"""
# category: simple charts
import altair as alt

# Compute x^2 + y^2 across a 2D grid
x, y = alt.pd.np.meshgrid(range(-5, 5), range(-5, 5))
z = x ** 2 + y ** 2

# Convert this grid to columnar data expected by Altair
data = alt.pd.DataFrame({'x': x.ravel(),
                     'y': y.ravel(),
                     'z': z.ravel()})

alt.Chart(data).mark_rect().encode(
    x='x:O',
    y='y:O',
    color='z:Q'
)
