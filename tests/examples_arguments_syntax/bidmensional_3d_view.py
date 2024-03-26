import altair as alt
import pandas as pd
import seaborn as sns
from vega_datasets import data

# Load and preprocess data
data_frame = data.cars().dropna()

data_frame['AdjustedHorsepower'] = data_frame['Horsepower'] // 20 * 20
data_frame['AdjustedWeightLbs'] = data_frame['Weight_in_lbs'] // 400 * 400
data_frame['CylinderCategory'] = data_frame['Cylinders'].apply(lambda value: "Less than 6" if value < 6 else "More than or equal to 6")

# Group and aggregate data
grouped_data = data_frame.groupby(['CylinderCategory', 'AdjustedHorsepower', 'AdjustedWeightLbs']).agg(
    AverageMPG=('Miles_per_Gallon', 'mean'),
    AverageAcceleration=('Acceleration', 'mean'),
    Count=('Name', 'count')
).reset_index()

# Variable declarations
weight_col = 'AdjustedWeightLbs'
horsepower_col = 'AdjustedHorsepower'
cylinder_col = 'CylinderCategory'
bubble_size_col = 'Count'

selected_cols = [weight_col, horsepower_col, cylinder_col, bubble_size_col]

transformed_data = pd.melt(grouped_data, selected_cols)

horsepower_values = sorted(transformed_data[horsepower_col].unique())

color_scheme = sns.color_palette("coolwarm", len(horsepower_values)).as_hex()

metrics = sorted(transformed_data['variable'].unique())

# Altair selections
horsepower_selection = alt.selection_point(fields=[horsepower_col], toggle=True)
interval_selection = alt.selection_interval()

metric_selection_bind = alt.binding_select(options=metrics)
metric_selection = alt.selection_point(name="SelectMetric", fields=['variable'], bind=metric_selection_bind, value=metrics[0])

# Legend for horsepower
legend = (alt.Chart(transformed_data[[horsepower_col]].drop_duplicates())
             .mark_rect()
             .encode(y=alt.Y(f'{horsepower_col}:O', axis=alt.Axis(orient='right', title=None)),
                     color=alt.Color(f'{horsepower_col}:O', scale=alt.Scale(domain=horsepower_values, range=color_scheme), legend=None),
                     opacity=alt.condition(horsepower_selection & interval_selection, alt.value(1.0), alt.value(0.1)))
             .properties(title='AdjustedHorsepower')
             .add_params(horsepower_selection, interval_selection))

# Cylinder charts
cylinder_values = sorted(transformed_data[cylinder_col].unique())
charts = []

for cylinder in cylinder_values:
    cylinder_data = transformed_data[transformed_data[cylinder_col] == cylinder]
    chart = (alt.Chart(cylinder_data)
               .mark_point()
               .encode(x=alt.X(f'{weight_col}:Q', scale=alt.Scale(zero=False)),
                       y=alt.Y('value:Q', scale=alt.Scale(zero=False), title='Selected metric value'),
                       color=alt.Color(f'{horsepower_col}:O', scale=alt.Scale(domain=horsepower_values, range=color_scheme), legend=None),
                       size=f'{bubble_size_col}:Q')
               .properties(title=f'{cylinder} Cylinders', width=400, height=400)
               .add_params(metric_selection)
               .transform_filter(metric_selection)
               .transform_filter(horsepower_selection & interval_selection)
               .interactive())
    charts.append(chart)

# Combine and display charts
alt.hconcat(legend, alt.hconcat(*charts).resolve_scale(x='shared', y='shared'))
