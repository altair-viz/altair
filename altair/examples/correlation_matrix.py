"""
Correlation matrix
------------------
This example shows how to create a correlation matrix and a heatmap from the iris dataset.
"""
# category: other charts
# Load packages
import altair as alt
import pandas as pd
from vega_datasets import data

## Section 1: Correlation plot

# Load the data
df_iris = data.iris()

corrMatrix = df_iris.corr().round(2).reset_index().rename(columns = {'index':'Var1'}).melt(id_vars = ['Var1'],
                                                                                                value_name = 'Corr',
                                                                                                var_name = 'Var2')

# Create the heatmap first
heatmap = alt.Chart(corrMatrix).mark_rect(
).encode(
    alt.X('Var1:O', title = ''),
    alt.Y('Var2:O', title = '', axis=alt.Axis(labelAngle=0)),
     alt.Color('Corr:Q',
                scale=alt.Scale(scheme='viridis'))
)

# Add the correlation values as a text mark
text = heatmap.mark_text(baseline='middle', fontSize=20).encode(
    text=alt.Text('Corr:Q', format='.2'),
    color=alt.condition(
        alt.datum['Corr'] >= 0.95,
        alt.value('black'),
        alt.value('white')
    )
)

# Set the height, width, title and other properties
corrMatrix_chart = (heatmap + text).properties(
    width = 400,
    height = 400,
    title = "Iris variables correlation matrix",
)
corrMatrix_chart.configure_axis(
    labelFontSize=18,
    titleFontSize=24,
).configure_title(
    fontSize=24,
    anchor='start',
).configure_legend(
    labelFontSize=20,
    titleFontSize=20)

## Section 2: Lower triangle of correlation plot with no diagonals

# This bit of wrangling creates a new dataframe with only half the elements
l1 = sorted(df_iris.corr().columns.to_list()) # sorting is needed to make sure the final correlation maps looks like an upper or lower triangle
l2 = l1.copy()
rows = []

for e1 in l1:
    for e2 in l2:
        rows.append([e1,e2, df_iris.corr().loc[e1,e2]])
    l2.remove(e1)
    
# Create dataframe from list of rows
newdf = pd.DataFrame(rows,columns=['Var1','Var2','Corr'])

# If you want to remove the diagonals
newdf = newdf[newdf['Var1']!=newdf['Var2']]

# Create the heatmap first
heatmap = alt.Chart(newdf).mark_rect(
).encode(
    alt.X('Var1:O', title = ''),
    alt.Y('Var2:O', title = '', axis=alt.Axis(labelAngle=0)),
     alt.Color('Corr:Q',
                scale=alt.Scale(scheme='viridis'))
)

# Add the correlation values as a text mark
text = heatmap.mark_text(baseline='middle', fontSize=20).encode(
    text=alt.Text('Corr:Q', format='.2'),
    color=alt.condition(
        alt.datum['Corr'] >= 0.95,
        alt.value('black'),
        alt.value('white')
    )
)

# Set the height, width, title and other properties
corrMatrix_chart = (heatmap + text).properties(
    width = 400,
    height = 400,
    title = "Iris variables correlation matrix",
)
corrMatrix_chart.configure_axis(
    labelFontSize=18,
    titleFontSize=24,
).configure_title(
    fontSize=24,
    anchor='start',
).configure_legend(
    labelFontSize=20,
    titleFontSize=20)

