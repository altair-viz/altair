.. _user-guide-data:

Specifying Data in Altair
-------------------------

.. currentmodule:: altair

Each top-level chart object (i.e. :class:`Chart`, :class:`LayerChart`,
and :class:`VConcatChart`, :class:`HConcatChart`, :class:`RepeatChart`,
:class:`FacetChart`) accepts a dataset as its first argument.
The dataset can be specified in one of the following ways:

- as a `Pandas DataFrame <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_
- as a :class:`Data` or related object (i.e. :class:`UrlData`, :class:`InlineData`, :class:`NamedData`)
- as a url string pointing to a ``json`` or ``csv`` formatted text file
- as an object that supports the `__geo_interface__` (eg. `Geopandas GeoDataFrame <http://geopandas.org/data_structures.html#geodataframe>`_, `Shapely Geometries <https://shapely.readthedocs.io/en/latest/manual.html#geometric-objects>`_, `GeoJSON Objects <https://github.com/jazzband/geojson#geojson-objects>`_)

For example, here we specify data via a DataFrame:

.. altair-plot::

   import altair as alt
   import pandas as pd

   data = pd.DataFrame({'x': ['A', 'B', 'C', 'D', 'E'],
                        'y': [5, 3, 6, 7, 2]})
   alt.Chart(data).mark_bar().encode(
       x='x',
       y='y',
   )

When data is specified as a DataFrame, the encoding is quite simple, as Altair
uses the data type information provided by Pandas to automatically determine
the data types required in the encoding.

By comparison, here we create the same chart using a :class:`Data` object,
with the data specified as a JSON-style list of records:

.. altair-plot::

   import altair as alt

   data = alt.Data(values=[{'x': 'A', 'y': 5},
                           {'x': 'B', 'y': 3},
                           {'x': 'C', 'y': 6},
                           {'x': 'D', 'y': 7},
                           {'x': 'E', 'y': 2}])
   alt.Chart(data).mark_bar().encode(
       x='x:O',  # specify ordinal data
       y='y:Q',  # specify quantitative data
   )

notice the extra markup required in the encoding; because Altair cannot infer
the types within a :class:`Data` object, we must specify them manually
(here we use :ref:`shorthand-description` to specify *ordinal* (``O``) for ``x``
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

You can use any URL visible to your frontend (i.e. JupyterLab, Jupyter Notebook, Colab, VSCode, Streamlit, etc.)

All of those frontends have different mechanisms for accessing local files (if they have a mechanism at all), so there is no way to provide general advice for how to proceed. By way of example, consider a JupyterLab setup with seattle-weather.csv and a notebook in the top level folder. In this case, the full URL needs to be given.

.. altair-plot::

    import altair as alt
    url = 'http://localhost:8888/files/seattle-weather.csv'

    alt.Chart(url).mark_bar().encode(
        x='month(date):O',
        y='count():Q',
        color='weather:N'
    )

We will further discuss encodings and associated types in :ref:`user-guide-encoding`, next.


.. _data-in-index:

Including Index Data
~~~~~~~~~~~~~~~~~~~~
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
turn it into a column using the ``reset_index()`` method of Pandas dataframes:

.. altair-plot::

   alt.Chart(data.reset_index()).mark_line().encode(
       x='index:T',
       y='value:Q'
   )

If the index object does not have a ``name`` attribute set, the resulting
column will be called ``"index"``.
More information is available in the
`Pandas documentation <http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.reset_index.html>`_.


.. _data-long-vs-wide:

Long-form vs. Wide-form Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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

Converting Between Long-form and Wide-form: Pandas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This sort of data manipulation can be done as a preprocessing step using Pandas_,
and is discussed in detail in the `Reshaping and Pivot Tables`_ section of the
Pandas documentation.

For converting wide-form data to the long-form data used by Altair, the ``melt``
method of dataframes can be used. The first argument to ``melt`` is the column
or list of columns to treat as index variables; the remaining columns will
be combined into an indicator variable and a value variable whose names can
be optionally specified:

.. altair-plot::
    :output: repr

    wide_form.melt('Date', var_name='company', value_name='price')

For more information on the ``melt`` method, see the `Pandas melt documentation`_.

In case you would like to undo this operation and convert from long-form back
to wide-form, the ``pivot`` method of dataframes is useful.

.. altair-plot::
    :output: repr

    long_form.pivot(index='Date', columns='company', values='price').reset_index()

For more information on the ``pivot`` method, see the `Pandas pivot documentation`_.

Converting Between Long-form and Wide-form: Fold Transform
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

.. _Pandas: http://pandas.pydata.org/
.. _Pandas pivot documentation: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.pivot.html
.. _Pandas melt documentation: https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.melt.html#pandas.DataFrame.melt
.. _Reshaping and Pivot Tables: https://pandas.pydata.org/pandas-docs/stable/reshaping.html

.. _data-geo-interface:

Geospatial Data
~~~~~~~~~~~~~~~
Working with geographical data in Altair is possible if the object contains a
`__geo_interface__` attribute. This attribute represents the geo_interface which is a
Python protocol for Geospatial Data. The protocol follows a GeoJSON-like structure to
store geo-spatial vector data.

To make working with Geospatial Data as similar as working with long-form structured data
the geo_interface is serialized in order to:
- make it be correctly interpreted by Altair
- provide users a similar experience as when working with tabular data such as Pandas.

Altair can interpret a spatial bounded entity (a Feature) or a list of Features
(FeatureCollection). In order for correct interpretation it is made sure that all records
contain a single geometry (one of Point, LineString, Polygon, MultiPoint,
MultiLineString, MultiPolygon, and GeometryCollection) and is stored as a Feature entity.

The most basic Feature is an entity that only contains a Geometry object. For example
a Polygon:

.. code:: python

    {
        "type": "Feature",
        "geometry": {
            "coordinates": [[
                [0, 0],
                [0, 2],
                [2, 2],
                [2, 0],
                [0, 0]
            ]],
            "type": "Polygon"
        }
    }

Often, the Feature contains also additional metadata next to the Geometry object.
The `__geo_interface__` provides two approaches to store metadata.
- Metadata stored as a dictionary within the key `properties` (so called properties
member). This properties member must exist in a valid Feature entity.
- Metada may be stored directly as foreign members on the top-level of the Feature.
There is no normative processing model for usage of this declaration.

Altair serializes the metadata from the properties in combination with the declared
geometry as Feature entities. The result of this approach is that the keys `type`
and `geometry` in the properties member will be overwritten if used.

So a `__geo_interface__` that is registered as such

.. code:: python

    {
        "type": "Feature",
        "id": "f1",
        "geometry": {...},
        "properties": {
            "id": 1,
            "foo": "xx",
            "bah": "yy",
            "type": "zz"
        },
        "title": "Example Feature"
    }

Is serialized as such:

.. code:: python

    {
        "type": "Feature",
        "geometry": {...},
        "foo": "xx",
        "bah": "yy",
        "id": 1
    }

The nested `"type": "zz"` in the properties member is overwritten by `"type":"Feature"`
and only the metadata stored in the properties member is serialized. Meaning that
foreign members and the commonly used identifier are not serialized.

.. _data-geopandas-vs-pandas:

GeoPandas vs Pandas
~~~~~~~~~~~~~~~~~~~
A `GeoDataFrame` is a `DataFrame` including a special column with spatial geometries.
The column-name containing the spatial geometries defaults to `geometry`. To directly
use a `GeoDataFrame` with Altair means in practice that only the column-name `type`
should be avoided.

.. _data-projections:

Projections
~~~~~~~~~~~
Altair works best when the Geospatial Data adopts the World Geodetic System 1984 as
its geographic coordinate reference system with units in decimal degrees.

Try to avoid putting projected data into Altair, but reproject your spatial data to
EPSG:4326 first.

If your data comes in a different projection (eg. with units in meters) and you don't
have the option to reproject the data, try using the project configuration
`(type: 'identity', reflectY': True)`. It draws the geometries in a cartesian grid
without applying a projection.

.. _data-winding-order:

Winding order
~~~~~~~~~~~~~
LineString, Polygon and MultiPolygon geometries contain coordinates in an order: lines
go in a certain direction, and polygon rings do too. The GeoJSON-like structure of the
__geo_interface__ recommends the right-hand rule winding order for Polygon and
MultiPolygons. Meaning that the exterior rings should be counterclockwise and interior
rings are clockwise. While it recommends the right-hand rule winding order, it does not
reject geometries that do not use the right-hand rule.

Altair does NOT follow the right-hand rule for geometries, but uses the left-hand rule.
Meaning that exterior rings should be clockwise and interior rings should be
counterclockwise.

If you face a problem regarding winding order, try to force the left-hand rule on your
data before usage in Altair using GeoPandas for example as such:

.. code:: python

    from shapely.ops import orient # version >=1.7a2
    gdf.geometry = gdf.geometry.apply(orient, args=(-1,))


.. _Protocol geo_interface: https://gist.github.com/sgillies/2217756
.. _Packages supporting the geo_interface: https://github.com/mlaloux/Python-geo_interface-applications
.. _The GeoJSON format: https://tools.ietf.org/html/rfc7946#section-3.1.9
