.. currentmodule:: altair
    
.. _user-guide-data:

Specifying Data
---------------

The basic data model used by Altair is tabular data,
similar to a spreadsheet or database table.
Individual datasets are assumed to contain a collection of records (rows),
which may contain any number of named data fields (columns).
Each top-level chart object (i.e. :class:`Chart`, :class:`LayerChart`,
:class:`VConcatChart`, :class:`HConcatChart`, :class:`RepeatChart`,
and :class:`FacetChart`) accepts a dataset as its first argument.

There are many different ways of specifying a dataset:

- as a `pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_
- as a DataFrame that supports the DataFrame Interchange Protocol (contains a ``__dataframe__`` attribute), e.g. polars and pyarrow. This is experimental.
- as a :class:`Data` or related object (i.e. :class:`UrlData`, :class:`InlineData`, :class:`NamedData`)
- as a url string pointing to a ``json`` or ``csv`` formatted text file
- as a `geopandas GeoDataFrame <http://geopandas.org/data_structures.html#geodataframe>`_, `Shapely Geometries <https://shapely.readthedocs.io/en/latest/manual.html#geometric-objects>`_, `GeoJSON Objects <https://github.com/jazzband/geojson#geojson-objects>`_ or other objects that support the ``__geo_interface__``
- as a generated dataset such as numerical sequences or geographic reference elements

When data is specified as a pandas DataFrame, Altair
uses the data type information provided by pandas to automatically determine
the data types required in the encoding. For example, here we specify data via a pandas DataFrame
and Altair automatically detects that the x-column should be visualized on a categorical (nominal) scale
and that the y-column should be visualized on a quantitative scale:

.. altair-plot::

   import altair as alt
   import pandas as pd

   data = pd.DataFrame({'x': ['A', 'B', 'C', 'D', 'E'],
                        'y': [5, 3, 6, 7, 2]})
   alt.Chart(data).mark_bar().encode(
       x='x',
       y='y',
   )

By comparison,
all other ways of specifying the data (including non-pandas DataFrames)
requires encoding types to be declared explicitly.
Here we create the same chart as above using a :class:`Data` object,
with the data specified as a JSON-style list of records:

.. altair-plot::

   import altair as alt

   data = alt.Data(values=[{'x': 'A', 'y': 5},
                           {'x': 'B', 'y': 3},
                           {'x': 'C', 'y': 6},
                           {'x': 'D', 'y': 7},
                           {'x': 'E', 'y': 2}])
   alt.Chart(data).mark_bar().encode(
       x='x:N',  # specify nominal data
       y='y:Q',  # specify quantitative data
   )

Notice the extra markup required in the encoding; because Altair cannot infer
the types within a :class:`Data` object, we must specify them manually
(here we use :ref:`shorthand-description` to specify *nominal* (``N``) for ``x``
and *quantitative* (``Q``) for ``y``; see :ref:`encoding-data-types`).

Similarly, we must also specify the data type when referencing data by URL:

.. altair-plot::

    import altair as alt
    from vega_datasets import data
    url = data.cars.url

    alt.Chart(url).mark_point().encode(
        x='Horsepower:Q',
        y='Miles_per_Gallon:Q'
    )

Encodings and their associated types are further discussed in :ref:`user-guide-encoding`.
Below we go into more detail about the different ways of specifying data in an Altair chart.

pandas DataFrame
~~~~~~~~~~~~~~~~

.. _data-in-index:

Including Index Data
^^^^^^^^^^^^^^^^^^^^
By design Altair only accesses dataframe columns, not dataframe indices.
At times, relevant data appears in the index. For example:

.. altair-plot::
   :output: repr

   import numpy as np
   rand = np.random.RandomState(0)

   data = pd.DataFrame({'value': rand.randn(100).cumsum()},
                       index=pd.date_range('2018', freq='D', periods=100))
   data.head()

If you would like the index to be available to the chart, you can explicitly
turn it into a column using the ``reset_index()`` method of pandas dataframes:

.. altair-plot::

   alt.Chart(data.reset_index()).mark_line().encode(
       x='index:T',
       y='value:Q'
   )

If the index object does not have a ``name`` attribute set, the resulting
column will be called ``"index"``.
More information is available in the
`pandas documentation <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.reset_index.html>`_.


.. _data-long-vs-wide:

Long-form vs. Wide-form Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
There are two common conventions for storing data in a dataframe, sometimes called
*long-form* and *wide-form*. Both are sensible patterns for storing data in
a tabular format; briefly, the difference is this:

- **wide-form data** has one row per *independent variable*, with metadata
  recorded in the *row and column labels*.
- **long-form data** has one row per *observation*, with metadata recorded
  within the table as *values*.

Altair's grammar works best with **long-form** data, in which each row
corresponds to a single observation along with its metadata.

A concrete example will help in making this distinction more clear.
Consider a dataset consisting of stock prices of several companies over time.
The wide-form version of the data might be arranged as follows:

.. altair-plot::
    :output: repr
    :chart-var-name: wide_form

    wide_form = pd.DataFrame({'Date': ['2007-10-01', '2007-11-01', '2007-12-01'],
                              'AAPL': [189.95, 182.22, 198.08],
                              'AMZN': [89.15, 90.56, 92.64],
                              'GOOG': [707.00, 693.00, 691.48]})
    print(wide_form)

Notice that each row corresponds to a single time-stamp (here time is the
independent variable), while metadata for each observation
(i.e. company name) is stored within the column labels.

The long-form version of the same data might look like this:

.. altair-plot::
    :output: repr
    :chart-var-name: long_form

    long_form = pd.DataFrame({'Date': ['2007-10-01', '2007-11-01', '2007-12-01',
                                       '2007-10-01', '2007-11-01', '2007-12-01',
                                       '2007-10-01', '2007-11-01', '2007-12-01'],
                              'company': ['AAPL', 'AAPL', 'AAPL',
                                          'AMZN', 'AMZN', 'AMZN',
                                          'GOOG', 'GOOG', 'GOOG'],
                              'price': [189.95, 182.22, 198.08,
                                         89.15,  90.56,  92.64,
                                        707.00, 693.00, 691.48]})
    print(long_form)

Notice here that each row contains a single observation (i.e. price), along
with the metadata for this observation (the date and company name).
Importantly, the column and index labels no longer contain any useful metadata.

As mentioned above, Altair works best with this long-form data, because relevant
data and metadata are stored within the table itself, rather than within the
labels of rows and columns:

.. altair-plot::

    alt.Chart(long_form).mark_line().encode(
      x='Date:T',
      y='price:Q',
      color='company:N'
    )

Wide-form data can be similarly visualized using e.g. layering
(see :ref:`layer-chart`), but it is far less convenient within Altair's grammar.

If you would like to convert data from wide-form to long-form, there are two possible
approaches: it can be done as a preprocessing step using pandas, or as a transform
step within the chart itself. We will detail to two approaches below.

.. _data-converting-long-form:

Converting with pandas
""""""""""""""""""""""
This sort of data manipulation can be done as a preprocessing step using pandas_,
and is discussed in detail in the `Reshaping and Pivot Tables`_ section of the
pandas documentation.

For converting wide-form data to the long-form data used by Altair, the ``melt``
method of dataframes can be used. The first argument to ``melt`` is the column
or list of columns to treat as index variables; the remaining columns will
be combined into an indicator variable and a value variable whose names can
be optionally specified:

.. altair-plot::
    :output: repr

    wide_form.melt('Date', var_name='company', value_name='price')

For more information on the ``melt`` method, see the `pandas melt documentation`_.

In case you would like to undo this operation and convert from long-form back
to wide-form, the ``pivot`` method of dataframes is useful.

.. altair-plot::
    :output: repr

    long_form.pivot(index='Date', columns='company', values='price').reset_index()

For more information on the ``pivot`` method, see the `pandas pivot documentation`_.

Converting with Fold Transform
""""""""""""""""""""""""""""""

If you would like to avoid data preprocessing, you can reshape your data using Altair's
Fold Transform (see :ref:`user-guide-fold-transform` for a full discussion).
With it, the above chart can be reproduced as follows:

.. altair-plot::

    alt.Chart(wide_form).transform_fold(
        ['AAPL', 'AMZN', 'GOOG'],
        as_=['company', 'price']
    ).mark_line().encode(
        x='Date:T',
        y='price:Q',
        color='company:N'
    )

Notice that unlike the pandas ``melt`` function we must explicitly specify the columns
to be folded. The ``as_`` argument is optional, with the default being ``["key", "value"]``.


.. _data-generated:

Generated Data
~~~~~~~~~~~~~~
At times it is convenient to not use an external data source, but rather generate data for
display within the chart specification itself. The benefit is that the chart specification
can be made much smaller for generated data than for embedded data.

Sequence Generator
^^^^^^^^^^^^^^^^^^
Here is an example of using the :func:`sequence` function to generate a sequence of  *x*
data, along with a :ref:`user-guide-calculate-transform` to compute *y* data.

.. altair-plot::

   import altair as alt

   # Note that the following generator is functionally similar to
   # data = pd.DataFrame({'x': np.arange(0, 10, 0.1)})
   data = alt.sequence(0, 10, 0.1, as_='x')

   alt.Chart(data).transform_calculate(
       y='sin(datum.x)'
   ).mark_line().encode(
       x='x:Q',
       y='y:Q',
   )

Graticule Generator
^^^^^^^^^^^^^^^^^^^
Another type of data that is convenient to generate in the chart itself is the latitude/longitude
lines on a geographic visualization, known as a graticule. These can be created using Altair's
:func:`graticule` generator function. Here is a simple example:

.. altair-plot::

   import altair as alt

   data = alt.graticule(step=[15, 15])

   alt.Chart(data).mark_geoshape(stroke='black').project(
       'orthographic',
       rotate=[0, -45, 0]
   )

Sphere Generator
^^^^^^^^^^^^^^^^
Finally when visualizing the globe a sphere can be used as a background layer
within a map to represent the extent of the Earth. This sphere data can be
created using Altair's :func:`sphere` generator function. Here is an example:

.. altair-plot::

   import altair as alt

   sphere_data = alt.sphere()
   grat_data = alt.graticule(step=[15, 15])

   background = alt.Chart(sphere_data).mark_geoshape(fill='aliceblue')
   lines = alt.Chart(grat_data).mark_geoshape(stroke='lightgrey')

   alt.layer(background, lines).project('naturalEarth1')

.. _pandas: http://pandas.pydata.org/
.. _pandas pivot documentation: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.pivot.html
.. _pandas melt documentation: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.melt.html#pandas.DataFrame.melt
.. _Reshaping and Pivot Tables: https://pandas.pydata.org/pandas-docs/stable/reshaping.html


Spatial Data
~~~~~~~~~~~~

In this section, we explain different methods for reading spatial data into Altair.
To learn more about how to work with this data after you have read it in,
please see the :ref:`user-guide-geoshape-marks` mark page.


.. _spatial-data-gdf:

GeoPandas GeoDataFrame
^^^^^^^^^^^^^^^^^^^^^^

It is convenient to use GeoPandas as the source for your spatial data.
GeoPandas can read many types of spatial data and Altair works well with GeoDataFrames.
Here we define four polygon geometries into a
GeoDataFrame and visualize these using the ``mark_geoshape``.

.. altair-plot::
   :output: repr

   from shapely import geometry
   import geopandas as gpd
   import altair as alt

   data_geoms = [
       {"color": "#F3C14F", "geometry": geometry.Polygon([[1.45, 3.75], [1.45, 0], [0, 0], [1.45, 3.75]])},
       {"color": "#4098D7", "geometry": geometry.Polygon([[1.45, 0], [1.45, 3.75], [2.57, 3.75], [2.57, 0], [2.33, 0], [1.45, 0]])},
       {"color": "#66B4E2", "geometry": geometry.Polygon([[2.33, 0], [2.33, 2.5], [3.47, 2.5], [3.47, 0], [3.2, 0], [2.57, 0], [2.33, 0]])},
       {"color": "#A9CDE0", "geometry": geometry.Polygon([[3.2, 0], [3.2, 1.25], [4.32, 1.25], [4.32, 0], [3.47, 0], [3.2, 0]])},
   ]

   gdf_geoms = gpd.GeoDataFrame(data_geoms)
   gdf_geoms


Since the spatial data in our example is not geographic,
we use ``project`` configuration ``type="identity", reflectY=True`` to draw the
geometries without applying a geographic projection. By using ``alt.Color(...).scale(None)`` we
disable the automatic color assignment in Altair
and instead directly use the provided Hex color codes.

.. altair-plot::

   alt.Chart(gdf_geoms, title="Vega-Altair").mark_geoshape().encode(
       alt.Color("color:N").scale(None)
   ).project(type="identity", reflectY=True)


.. _spatial-data-inline-geojson:

Inline GeoJSON Object
^^^^^^^^^^^^^^^^^^^^^

If your source data is a GeoJSON file and you do not want to load it
into a GeoPandas GeoDataFrame you can provide it as a dictionary to the Altair ``Data`` class. A
GeoJSON file normally consists of a ``FeatureCollection`` with a list of
``features`` where the information for each geometry is specified within a
``properties`` dictionary. In the following example a GeoJSON-like data
object is specified into a ``Data`` class using the ``property``
value of the ``key`` that contain the nested list (here named
``features``).

.. altair-plot::
   :output: repr

   obj_geojson = {
       "type": "FeatureCollection",
       "features":[
           {"type": "Feature", "properties": {"location": "left"}, "geometry": {"type": "Polygon", "coordinates": [[[1.45, 3.75], [1.45, 0], [0, 0], [1.45, 3.75]]]}},
           {"type": "Feature", "properties": {"location": "middle-left"}, "geometry": {"type": "Polygon", "coordinates": [[[1.45, 0], [1.45, 3.75], [2.57, 3.75], [2.57, 0], [2.33, 0], [1.45, 0]]]}},
           {"type": "Feature", "properties": {"location": "middle-right"}, "geometry": {"type": "Polygon", "coordinates": [[[2.33, 0], [2.33, 2.5], [3.47, 2.5], [3.47, 0], [3.2, 0], [2.57, 0], [2.33, 0]]]}},
           {"type": "Feature", "properties": {"location": "right"}, "geometry": {"type": "Polygon", "coordinates": [[[3.2, 0], [3.2, 1.25], [4.32, 1.25], [4.32, 0], [3.47, 0], [3.2, 0]]]}}
       ]
   }
   data_obj_geojson = alt.Data(values=obj_geojson, format=alt.DataFormat(property="features"))
   data_obj_geojson

The label for each objects location is stored within the ``properties`` dictionary. To access these values
you can specify a nested variable name (here ``properties.location``) within the color
channel encoding. Here we change the coloring encoding to be based on this location label,
and apply a ``magma`` color scheme instead of the default one.
The ``:O`` suffix indicates that we want Altair to treat these values as ordinal,
and you can read more about it in the :ref:`encoding-data-types` page.
for the ordinal structured data.

.. altair-plot::

   alt.Chart(data_obj_geojson, title="Vega-Altair - ordinal scale").mark_geoshape().encode(
       alt.Color("properties.location:O").scale(scheme='magma')
   ).project(type="identity", reflectY=True)


.. _spatial-data-remote-geojson:

GeoJSON File by URL
^^^^^^^^^^^^^^^^^^^

Altair can load GeoJSON resources directly from a web URL. Here we use
an example from geojson.xyz. As is explained in :ref:`spatial-data-inline-geojson`,
we specify ``features`` as
the value for the ``property`` parameter in the ``alt.DataFormat()`` object
and prepend the attribute we want to plot (``continent``)
with the name of the nested dictionary where the
information of each geometry is stored (``properties``).

.. altair-plot::
   :output: repr

   url_geojson = "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_110m_admin_0_countries.geojson"
   data_url_geojson = alt.Data(url=url_geojson, format=alt.DataFormat(property="features"))
   data_url_geojson

.. altair-plot::

    alt.Chart(data_url_geojson).mark_geoshape().encode(color='properties.continent:N')


.. _spatial-data-inline-topojson:

Inline TopoJSON Object
^^^^^^^^^^^^^^^^^^^^^^

TopoJSON is an extension of GeoJSON, where the geometry of the features
are referred to from a top-level object named arcs. Each shared arc is
only stored once to reduce the size of the data. A TopoJSON file object can contain
multiple objects (eg. boundary border and province border). When
defining a TopoJSON object for Altair we specify the ``topojson``
data format type and the name of the object we like to visualize using the
``feature`` parameter. Here the name of this object key is ``MY_DATA``,
but this differs in each dataset.

.. altair-plot::
   :output: repr

   obj_topojson = {
       "arcs": [
           [[1.0, 1.0], [0.0, 1.0], [0.0, 0.0], [1.0, 0.0]],
           [[1.0, 0.0], [2.0, 0.0], [2.0, 1.0], [1.0, 1.0]],
           [[1.0, 1.0], [1.0, 0.0]],
       ],
       "objects": {
           "MY_DATA": {
               "geometries": [
                   {"arcs": [[-3, 0]], "properties": {"name": "abc"}, "type": "Polygon"},
                   {"arcs": [[1, 2]], "properties": {"name": "def"}, "type": "Polygon"},
               ],
               "type": "GeometryCollection",
           }
       },
       "type": "Topology",
   }
   data_obj_topojson = alt.Data(
       values=obj_topojson, format=alt.DataFormat(feature="MY_DATA", type="topojson")
   )
   data_obj_topojson

.. altair-plot::

   alt.Chart(data_obj_topojson).mark_geoshape(
   ).encode(
       color="properties.name:N"
   ).project(
       type='identity', reflectY=True
   )


.. _spatial-data-remote-topojson:

TopoJSON File by URL
^^^^^^^^^^^^^^^^^^^^

Altair can load TopoJSON resources directly from a web URL. As
explained in :ref:`spatial-data-inline-topojson`, we have to use the
``feature`` parameter to specify the object name (here ``boroughs``) and
define the type of data as ``topjoson`` in the ``alt.DataFormat()`` object.

.. altair-plot::
   :output: repr

   from vega_datasets import data

   url_topojson = data.londonBoroughs.url

   data_url_topojson = alt.Data(
       url=url_topojson, format=alt.DataFormat(feature="boroughs", type="topojson")
   )

   data_url_topojson

Note: There also exist a shorthand to extract the objects from a
topojson file if this file is accessible by URL:
``alt.topo_feature(url=url_topojson, feature="boroughs")``

We color encode the Boroughs by there names as they are stored as an
unique identifier (``id``). We use a ``symbolLimit`` of 33 in two
columns to display all entries in the legend
and change the color scheme to have more distinct colors.
We also add a tooltip which shows the name of the borough
as we hover over it with the mouse.

.. altair-plot::

   alt.Chart(data_url_topojson, title="London-Boroughs").mark_geoshape(
       tooltip=True
   ).encode(
       alt.Color("id:N").scale(scheme='tableau20').legend(columns=2, symbolLimit=33)
   )

Similar to the ``feature`` option, there also exists the ``mesh``
parameter. This parameter extracts a named TopoJSON object set.
Unlike the feature option, the corresponding geo data is returned as
a single, unified mesh instance, not as individual GeoJSON features.
Extracting a mesh is useful for more efficiently drawing borders
or other geographic elements that you do not need to associate with
specific regions such as individual countries, states or counties.

Here below we draw the same Boroughs of London, but now as mesh only.

Note: you have to explicitly define ``filled=False`` to draw multi(lines)
without fill color.

.. altair-plot::

   from vega_datasets import data

   url_topojson = data.londonBoroughs.url

   data_url_topojson_mesh = alt.Data(
       url=url_topojson, format=alt.DataFormat(mesh="boroughs", type="topojson")
   )

   alt.Chart(data_url_topojson_mesh, title="Border London-Boroughs").mark_geoshape(
       filled=False
   )

.. _spatial-data-nested-geojson:

Nested GeoJSON Objects
^^^^^^^^^^^^^^^^^^^^^^

GeoJSON data can also be nested within another dataset. In this case it
is possible to use the ``shape`` encoding channel in combination with the
``:G`` suffix to visualize the nested features as GeoJSON objects.
In the following example the GeoJSON object are nested within ``geo``
in the list of dictionaries:

.. altair-plot::

   nested_features = [
       {"color": "#F3C14F", "geo": {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[1.45, 3.75], [1.45, 0], [0, 0], [1.45, 3.75]]]}}},
       {"color": "#4098D7", "geo": {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[1.45, 0], [1.45, 3.75], [2.57, 3.75], [2.57, 0], [2.33, 0], [1.45, 0]]]}}},
       {"color": "#66B4E2", "geo": {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[2.33, 0], [2.33, 2.5], [3.47, 2.5], [3.47, 0], [3.2, 0], [2.57, 0], [2.33, 0]]]}}},
       {"color": "#A9CDE0", "geo": {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [[[3.2, 0], [3.2, 1.25], [4.32, 1.25], [4.32, 0], [3.47, 0], [3.2, 0]]]}}},
   ]
   data_nested_features = alt.Data(values=nested_features)

   alt.Chart(data_nested_features, title="Vega-Altair").mark_geoshape().encode(
       shape="geo:G",
       color=alt.Color("color:N").scale(None)
   ).project(type="identity", reflectY=True)


.. _data-projections:

Projections
^^^^^^^^^^^
For geographic data it is best to use the World Geodetic System 1984 as
its geographic coordinate reference system with units in decimal degrees.
Try to avoid putting projected data into Altair, but reproject your spatial data to
EPSG:4326 first.
If your data comes in a different projection (eg. with units in meters) and you don't
have the option to reproject the data, try using the project configuration
``(type: 'identity', reflectY': True)``. It draws the geometries without applying a projection.


.. _data-winding-order:

Winding Order
^^^^^^^^^^^^^
LineString, Polygon and MultiPolygon geometries contain coordinates in an order: lines
go in a certain direction, and polygon rings do too. The GeoJSON-like structure of the
``__geo_interface__`` recommends the right-hand rule winding order for Polygon and
MultiPolygons. Meaning that the exterior rings should be counterclockwise and interior
rings are clockwise. While it recommends the right-hand rule winding order, it does not
reject geometries that do not use the right-hand rule.

Altair does NOT follow the right-hand rule for geometries, but uses the left-hand rule.
Meaning that exterior rings should be clockwise and interior rings should be
counterclockwise.
If you face a problem regarding winding order, try to force the left-hand rule on your
data before usage in Altair using GeoPandas for example as such:

.. code:: python

    from shapely.ops import orient
    gdf.geometry = gdf.geometry.apply(orient, args=(-1,))

.. toctree::
   :maxdepth: 1
   :caption: User Guide
   :hidden:

   self
   encodings/index
   marks/index
   transform/index
   color_usage
   interactions
   compound_charts
   scale_resolve
   times_and_dates
   customization
   configuration
   saving_charts
   jupyter_chart


.. toctree::
   :maxdepth: 1
   :caption: Advanced Usage
   :hidden:

   internals
   display_frontends
   custom_renderers
   data_transformers
   large_datasets
