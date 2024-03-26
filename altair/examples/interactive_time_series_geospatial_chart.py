"""
Interactive time series geospatial chart 
----------------------------------------

This example shows how to use range slider that lets you choose a day which is used by the selection to select data only for that day to visualize surge in per-capita cases of covid-19. The marks are custom SVG shapes (a vertical line) on a geospatial plot (it looks like a bar plot on a map). Slide the slider knob to see how the selection changes the data and hence the plot.
"""
# category: interactive charts

import altair as alt
import pandas as pd
import geopandas as gpd

alt.data_transformers.enable("json", urlpath="files")

# Getting the states data and shapefiles for the base states layer
states_shp_uri = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"
states = gpd.read_file(states_shp_uri)

# Making latitudes and longitudes for text layer
states["lon"] = states["geometry"].centroid.x
states["lat"] = states["geometry"].centroid.y

# Albers USA projection does not support the regions with the following IDs
states = states[
    ~(
        (states["id"] == "69")
        | (states["id"] == "78")
        | (states["id"] == "60")
        | (states["id"] == "72")
        | (states["id"] == "66")
    )
]

# Load the covid data - It is processed to show per-capita cases of the past two weeks. The dataset has data from 15 Oct 2020 to 27 Oct 2020. The data was then filtered on per-capita values >= 4.5 (representing a high surge)
# This data also contains a "height" column with SVG string representing the 'past_2_weeks_per_capita' (scaled up for visualization)
# The SVG string used for this is a simple vertical line: "M 0 0 L 0 -1"
# An example of making the "heights" column from the raw data could be - data.assign(height = data['past_2_weeks_per_capita'].apply(lambda x: f"M 0 0 L 0 -{x*1.05}"))
plot_data = pd.read_csv("past_2_weeks_per_capita.csv")

# Base layer is a simple grey states data
base = (
    alt.Chart(states)
    .mark_geoshape(fill="#ededed", stroke="white")
    .encode()
    .project("albersUsa")
)

# Text layer is names of the states centered on longitudes and latitudes calculated earlier
text = base.mark_text().encode(text="name:N", longitude="lon:Q", latitude="lat:Q")


def timestamp(t):
    return pd.to_datetime(t).timestamp() * 1000


# Range slider that lets you choose dates while sliding the knob
slider = alt.binding_range(
    name="till_date:",
    step=1 * 24 * 60 * 60 * 1000,
    min=timestamp(min(plot_data["date"])),
    max=timestamp(max(plot_data["date"])),
)

# Selects data for the given date chosen by the slider
day = alt.selection_single(
    bind=slider,
    name="slider",
    fields=["date"],
    init={"date": timestamp(min(plot_data["date"]))},
)

# Custom SVG marker layer : It looks like a bar chart on a geospatial plot
spikes = (
    alt.Chart(plot_data)
    .mark_point(
        fillOpacity=0.3, fill="red", strokeOpacity=1, strokeWidth=2.5, stroke="red"
    )
    .encode(
        latitude="lat:Q",
        longitude="lon:Q",
        shape=alt.Shape("height:N", scale=None),
    )
    .add_selection(day)
    .transform_filter(
        "(year(datum.date) == year(slider.date[0])) && (month(datum.date) == month(slider.date[0])) && (date(datum.date) == date(slider.date[0]))"
    )
)

(base + text + spikes).properties(width=800, height=800).configure_view(stroke=None)
