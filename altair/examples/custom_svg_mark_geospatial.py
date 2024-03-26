"""
Custom SVG marks on Geospatial Plot
-----------------------------------

This example shows how to use custom SVG shapes as marks on Geospatial plots. 
"""
# category: maps, other charts

import altair as alt
import pandas as pd
import geopandas as gpd

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

# Getting covid cases data for 6th April 2021
# This data also contains a "height" column with SVG string representing the 'cases' (scaled down for visualization)
# The SVG string used for this is a baseless triangle: "M -1 0 L 0 -1 L 1 0"
# An example of making the "heights" column from the raw data could be - data.assign(height = data['cases'].apply(lambda x: f"M -1 0 L 0 -{x/10000} L 1 0"))
plot_data = pd.read_csv("covid_cases_april_6.csv")

# Base layer is a simple grey states data
base = (
    alt.Chart(states)
    .mark_geoshape(fill="#ededed", stroke="white")
    .encode()
    .project("albersUsa")
)

# Text layer is names of the states centered on longitudes and latitudes calculated earlier
text = base.mark_text().encode(text="name:N", longitude="lon:Q", latitude="lat:Q")

# CUstom SVG marker layer
spikes = (
    alt.Chart(plot_data)
    .mark_point(
        fillOpacity=0.5,
        fill="red",
        strokeOpacity=1,
        strokeWidth=1,
        stroke="red",
    )
    .encode(
        shape=alt.Shape("height", scale=None),  # Scaling it to None is important
        longitude="lon:Q",
        latitude="lat:Q",
    )
    .properties(width=800, height=500)
)

(base + text + spikes).configure_view(stroke=None)
