.. currentmodule:: altair

.. _user-guide-encoding:

Encodings
---------

The key to creating meaningful visualizations is to map *properties of the data*
to *visual properties* in order to effectively communicate information.
In Altair, this mapping of visual properties to data columns is referred to
as an **encoding**, and is most often expressed through the :meth:`Chart.encode`
method.

For example, here we will visualize the cars dataset using four of the available
encodings: ``x`` (the x-axis value), ``y`` (the y-axis value),
``color`` (the color of the marker), and ``shape`` (the shape of the point marker):

.. altair-plot::

   import altair as alt
   from vega_datasets import data
   cars = data.cars()

   alt.Chart(cars).mark_point().encode(
       x='Horsepower',
       y='Miles_per_Gallon',
       color='Origin',
       shape='Origin'
   )

For data specified as a DataFrame, Altair can automatically determine the
correct data type for each encoding, and creates appropriate scales and
legends to represent the data.

.. _encoding-channels:

Encoding Channels
~~~~~~~~~~~~~~~~~

Altair provides a number of encoding channels that can be useful in different
circumstances; the following table summarizes them:

Position Channels
^^^^^^^^^^^^^^^^^

==========  ===================  =================================  ===================================
Channel     Altair Class         Description                        Example
==========  ===================  =================================  ===================================
x           :class:`X`           The x-axis value                   :ref:`gallery_scatter_tooltips`
y           :class:`Y`           The y-axis value                   :ref:`gallery_scatter_tooltips`
x2          :class:`X2`          Second x value for ranges          :ref:`gallery_gantt_chart`
y2          :class:`Y2`          Second y value for ranges          :ref:`gallery_candlestick_chart`
longitude   :class:`Longitude`   Longitude for geo charts           :ref:`gallery_point_map`
latitude    :class:`Latitude`    Latitude for geo charts            :ref:`gallery_point_map`
longitude2  :class:`Longitude2`  Second longitude value for ranges  :ref:`gallery_airport_connections`
latitude2   :class:`Latitude2`   Second latitude value for ranges   :ref:`gallery_airport_connections`
xError      :class:`XError`      The x-axis error value             N/A
yError      :class:`YError`      The y-axis error value             N/A
xError2     :class:`XError2`     The second x-axis error value      N/A
yError2     :class:`YError2`     The second y-axis error value      N/A
xOffset     :class:`XOffset`     Offset to the x position           :ref:`gallery_grouped_bar_chart2`
yOffset     :class:`YOffset`     Offset to the y position           :ref:`gallery_strip_plot_jitter`
theta       :class:`Theta`       The start arc angle                :ref:`gallery_radial_chart`
theta2      :class:`Theta2`      The end arc angle (radian)         :ref:`gallery_pacman_chart`
==========  ===================  =================================  ===================================

Mark Property Channels
^^^^^^^^^^^^^^^^^^^^^^

=============  ======================  ==============================  =========================================
Channel        Altair Class            Description                     Example
=============  ======================  ==============================  =========================================
angle          :class:`Angle`          The angle of the mark           :ref:`gallery_wind_vector_map`
color          :class:`Color`          The color of the mark           :ref:`gallery_simple_heatmap`
fill           :class:`Fill`           The fill for the mark           :ref:`gallery_ridgeline_plot`
fillopacity    :class:`FillOpacity`    The opacity of the mark's fill  N/A
opacity        :class:`Opacity`        The opacity of the mark         :ref:`gallery_horizon_graph`
radius         :class:`Radius`         The radius or the mark          :ref:`gallery_radial_chart`
shape          :class:`Shape`          The shape of the mark           :ref:`gallery_us_incomebrackets_by_state_facet`
size           :class:`Size`           The size of the mark            :ref:`gallery_table_bubble_plot_github`
stroke         :class:`Stroke`         The stroke of the mark          N/A
strokeDash     :class:`StrokeDash`     The stroke dash style           :ref:`gallery_multi_series_line`
strokeOpacity  :class:`StrokeOpacity`  The opacity of the line         N/A
strokeWidth    :class:`StrokeWidth`    The width of the line           N/A
=============  ======================  ==============================  =========================================

Text and Tooltip Channels
^^^^^^^^^^^^^^^^^^^^^^^^^

=======  ================  ========================  =========================================
Channel  Altair Class      Description               Example
=======  ================  ========================  =========================================
text     :class:`Text`     Text to use for the mark  :ref:`gallery_scatter_with_labels`
key      :class:`Key`      --                        N/A
tooltip  :class:`Tooltip`  The tooltip value         :ref:`gallery_scatter_tooltips`
=======  ================  ========================  =========================================

Hyperlink Channel
^^^^^^^^^^^^^^^^^

=======  ================  ========================  =========================================
Channel  Altair Class      Description               Example
=======  ================  ========================  =========================================
href     :class:`Href`     Hyperlink for  points     :ref:`gallery_scatter_href`
=======  ================  ========================  =========================================

Level of Detail Channel
^^^^^^^^^^^^^^^^^^^^^^^

=======  ================  ===============================  =========================================
Channel  Altair Class      Description                      Example
=======  ================  ===============================  =========================================
detail   :class:`Detail`   Additional property to group by  :ref:`gallery_ranged_dot_plot`
=======  ================  ===============================  =========================================

Order Channel
^^^^^^^^^^^^^

=======  ================  =============================  =====================================
Channel  Altair Class      Description                    Example
=======  ================  =============================  =====================================
order    :class:`Order`    Sets the order of the marks    :ref:`gallery_connected_scatterplot`
=======  ================  =============================  =====================================

Facet Channels
^^^^^^^^^^^^^^

=======  ================  ===============================================  =============================================
Channel  Altair Class      Description                                      Example
=======  ================  ===============================================  =============================================
column   :class:`Column`   The column of a faceted plot                     :ref:`gallery_trellis_scatter_plot`
row      :class:`Row`      The row of a faceted plot                        :ref:`gallery_beckers_barley_trellis_plot`
facet    :class:`Facet`    The row and/or column of a general faceted plot  :ref:`gallery_us_population_over_time_facet`
=======  ================  ===============================================  =============================================

.. _encoding-data-types:

Encoding Data Types
~~~~~~~~~~~~~~~~~~~
The details of any mapping depend on the *type* of the data. Altair recognizes
five main data types:

============  ==============  ================================================
Data Type     Shorthand Code  Description
============  ==============  ================================================
quantitative  ``Q``           a continuous real-valued quantity
ordinal       ``O``           a discrete ordered quantity
nominal       ``N``           a discrete unordered category
temporal      ``T``           a time or date value
geojson       ``G``           a geographic shape
============  ==============  ================================================

If types are not specified for data input as a DataFrame, Altair defaults to
``quantitative`` for any numeric data, ``temporal`` for date/time data, and
``nominal`` for string data, but be aware that these defaults are by no means
always the correct choice!

The types can either be expressed in a long-form using the channel encoding
classes such as :class:`X` and :class:`Y`, or in short-form using the
:ref:`Shorthand Syntax <shorthand-description>` discussed below.
For example, the following two methods of specifying the type will lead to
identical plots:

.. altair-plot::

   alt.Chart(cars).mark_point().encode(
       x='Acceleration:Q',
       y='Miles_per_Gallon:Q',
       color='Origin:N'
   )

.. altair-plot::

  alt.Chart(cars).mark_point().encode(
      alt.X('Acceleration', type='quantitative'),
      alt.Y('Miles_per_Gallon', type='quantitative'),
      alt.Color('Origin', type='nominal')
  )

The shorthand form, ``x="name:Q"``, is useful for its lack of boilerplate
when doing quick data explorations. The long-form,
``alt.X('name', type='quantitative')``, is useful when doing more fine-tuned
adjustments to the encoding, such as binning, axis and scale properties,
or more.

Specifying the correct type for your data is important, as it affects the
way Altair represents your encoding in the resulting plot.

.. _type-legend-scale:

Effect of Data Type on Color Scales
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
As an example of this, here we will represent the same data three different ways,
with the color encoded as a *quantitative*, *ordinal*, and *nominal* type,
using three vertically-concatenated charts (see :ref:`vconcat-chart`):

.. altair-plot::

   base = alt.Chart(cars).mark_point().encode(
       x='Horsepower:Q',
       y='Miles_per_Gallon:Q',
   ).properties(
       width=150,
       height=150
   )

   alt.vconcat(
      base.encode(color='Cylinders:Q').properties(title='quantitative'),
      base.encode(color='Cylinders:O').properties(title='ordinal'),
      base.encode(color='Cylinders:N').properties(title='nominal'),
   )

The type specification influences the way Altair, via Vega-Lite, decides on
the color scale to represent the value, and influences whether a discrete
or continuous legend is used.

.. _type-axis-scale:

Effect of Data Type on Axis Scales
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Similarly, for x and y axis encodings, the type used for the data will affect
the scales used and the characteristics of the mark. For example, here is the
difference between a ``quantitative`` and ``ordinal`` scale for an column
that contains integers specifying a year:

.. altair-plot::

    pop = data.population.url

    base = alt.Chart(pop).mark_bar().encode(
        alt.Y('mean(people):Q', title='total population')
    ).properties(
        width=200,
        height=200
    )

    alt.hconcat(
        base.encode(x='year:Q').properties(title='year=quantitative'),
        base.encode(x='year:O').properties(title='year=ordinal')
    )

Because quantitative values do not have an inherent width, the bars do not
fill the entire space between the values.
This view also makes clear the missing year of data that was not immediately
apparent when we treated the years as categories.

This kind of behavior is sometimes surprising to new users, but it emphasizes
the importance of thinking carefully about your data types when visualizing
data: a visual encoding that is suitable for categorical data may not be
suitable for quantitative data, and vice versa.


.. _encoding-channel-options:

Encoding Channel Options
~~~~~~~~~~~~~~~~~~~~~~~~
Each encoding channel allows for a number of additional options to be expressed;
these can control things like axis properties, scale properties, headers and
titles, binning parameters, aggregation, sorting, and many more.

The particular options that are available vary by encoding type; the various
options are listed below.

X and Y
^^^^^^^

The :class:`X` and :class:`Y` encodings accept the following options:

.. altair-object-table:: altair.PositionFieldDef

Color, Fill, and Stroke
^^^^^^^^^^^^^^^^^^^^^^^

The :class:`Color`, :class:`Fill`, and :class:`Stroke`  encodings accept the following options:

.. altair-object-table:: altair.FieldOrDatumDefWithConditionMarkPropFieldDefGradientstringnull

Shape
^^^^^

The :class:`Shape` encoding accepts the following options:

.. altair-object-table:: altair.FieldOrDatumDefWithConditionMarkPropFieldDefTypeForShapestringnull

Order
^^^^^

The :class:`Order` encoding accepts the following options:

.. altair-object-table:: altair.OrderFieldDef

Angle, FillOpacity, Opacity, Size, StrokeOpacity, and StrokeWidth
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`Angle`, :class:`FillOpacity`, :class:`Opacity`, :class:`Size`, :class:`StrokeOpacity`,
and :class:`StrokeWidth` encodings accept the following options:

.. altair-object-table:: altair.FieldOrDatumDefWithConditionMarkPropFieldDefnumber

StrokeDash
^^^^^^^^^^

The :class:`StrokeDash` encoding accepts the following options:

.. altair-object-table:: altair.FieldOrDatumDefWithConditionMarkPropFieldDefnumberArray

Row and Column
^^^^^^^^^^^^^^

The :class:`Row` and :class:`Column`, and :class:`Facet` encodings accept the following options:

.. altair-object-table:: altair.RowColumnEncodingFieldDef

Facet
^^^^^

The :class:`Facet` encoding accepts the following options:

.. altair-object-table:: altair.FacetEncodingFieldDef

Text
^^^^

The :class:`Text` encoding accepts the following options:

.. altair-object-table:: altair.FieldOrDatumDefWithConditionStringFieldDefText

Description, Href, Tooltip, Url
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`Description`, :class:`Href`, :class:`Tooltip`, and :class:`Url` encodings accept the following options:

.. altair-object-table:: altair.StringFieldDefWithCondition

Detail and Key
^^^^^^^^^^^^^^

The :class:`Detail` and :class:`Key` encodings accept the following options:

.. altair-object-table:: altair.FieldDefWithoutScale

Latitude and Longitude
^^^^^^^^^^^^^^^^^^^^^^

The :class:`Latitude` and :class:`Longitude` encodings accept the following options:

.. altair-object-table:: altair.LatLongFieldDef

Radius and Theta
^^^^^^^^^^^^^^^^

The :class:`Radius` and :class:`Theta` encodings accept the following options:

.. altair-object-table:: altair.PositionFieldDefBase

Latitude2, Longitude2, Radius2, Theta2, X2, Y2, XError, YError, XError2, and YError2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`Latitude2`, :class:`Longitude2`, :class:`Radius2`, :class:`Theta2`, :class:`X2`, :class:`Y2`, :class:`XError`, :class:`YError`, :class:`XError2`, and :class:`YError2` encodings accept the following options:

.. altair-object-table:: altair.SecondaryFieldDef


.. _encoding-aggregates:

Binning and Aggregation
~~~~~~~~~~~~~~~~~~~~~~~

Beyond simple channel encodings, Altair's visualizations are built on the
concept of the database-style grouping and aggregation; that is, the
`split-apply-combine <https://www.jstatsoft.org/article/view/v040i01>`_
abstraction that underpins many data analysis approaches.

For example, building a histogram from a one-dimensional dataset involves
splitting data based on the bin it falls in, aggregating the results within
each bin using a *count* of the data, and then combining the results into
a final figure.

In Altair, such an operation looks like this:

.. altair-plot::

   alt.Chart(cars).mark_bar().encode(
       alt.X('Horsepower', bin=True),
       y='count()'
       # could also use alt.Y(aggregate='count', type='quantitative')
   )

Notice here we use the shorthand version of expressing an encoding channel
(see :ref:`shorthand-description`) with the ``count`` aggregation,
which is the one aggregation that does not require a field to be
specified.

Similarly, we can create a two-dimensional histogram using, for example, the
size of points to indicate counts within the grid (sometimes called
a "Bubble Plot"):

.. altair-plot::

   alt.Chart(cars).mark_point().encode(
       alt.X('Horsepower', bin=True),
       alt.Y('Miles_per_Gallon', bin=True),
       size='count()',
   )

There is no need, however, to limit aggregations to counts alone. For example,
we could similarly create a plot where the color of each point
represents the mean of a third quantity, such as acceleration:

.. altair-plot::

   alt.Chart(cars).mark_circle().encode(
       alt.X('Horsepower', bin=True),
       alt.Y('Miles_per_Gallon', bin=True),
       size='count()',
       color='average(Acceleration):Q'
   )

For a full list of available aggregates, see :ref:`agg-func-table`.


.. _shorthand-description:

Encoding Shorthands
~~~~~~~~~~~~~~~~~~~

For convenience, Altair allows the specification of the variable name along
with the aggregate and type within a simple shorthand string syntax.
This makes use of the type shorthand codes listed in :ref:`encoding-data-types`
as well as the aggregate names listed in :ref:`agg-func-table`.
The following table shows examples of the shorthand specification alongside
the long-form equivalent:

===================  =======================================================
Shorthand            Equivalent long-form
===================  =======================================================
``x='name'``         ``alt.X('name')``
``x='name:Q'``       ``alt.X('name', type='quantitative')``
``x='sum(name)'``    ``alt.X('name', aggregate='sum')``
``x='sum(name):Q'``  ``alt.X('name', aggregate='sum', type='quantitative')``
``x='count():Q'``    ``alt.X(aggregate='count', type='quantitative')``
===================  =======================================================


.. _ordering-channels:

Ordering Marks
~~~~~~~~~~~~~~

The `order` option and :class:`Order` channel can sort how marks are drawn on the chart.

For stacked marks, this controls the order of components of the stack. Here, the elements of each bar are sorted alphabetically by the name of the nominal data in the color channel.

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    barley = data.barley()

    alt.Chart(barley).mark_bar().encode(
        x='variety:N',
        y='sum(yield):Q',
        color='site:N',
        order=alt.Order("site", sort="ascending")
    )

The order can be reversed by changing the sort option to `descending`.

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    barley = data.barley()

    alt.Chart(barley).mark_bar().encode(
        x='variety:N',
        y='sum(yield):Q',
        color='site:N',
        order=alt.Order("site", sort="descending")
    )

The same approach works for other mark types, like stacked areas charts.

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    barley = data.barley()

    alt.Chart(barley).mark_area().encode(
        x='variety:N',
        y='sum(yield):Q',
        color='site:N',
        order=alt.Order("site", sort="ascending")
    )

For line marks, the `order` channel encodes the order in which data points are connected. This can be useful for creating a scatterplot that draws lines between the dots using a different field than the x and y axes.

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    driving = data.driving()

    alt.Chart(driving).mark_line(point=True).encode(
        alt.X('miles', scale=alt.Scale(zero=False)),
        alt.Y('gas', scale=alt.Scale(zero=False)),
        order='year'
    )

Sorting
~~~~~~~

Specific channels can take a  :class:`sort` property which determines the
order of the scale being used for the channel. There are a number of different
sort options available:

- ``sort='ascending'`` (Default) will sort the field's value in ascending order.
  for string data, this uses standard alphabetical order.
- ``sort='descending'`` will sort the field's value in descending order
- passing the name of an encoding channel to ``sort``, such as ``"x"`` or ``"y"``, allows for 
  sorting by that channel. An optional minus prefix can be used for a descending 
  sort. For example ``sort='-x'`` would sort by the x channel in descending order.
- passing a list to ``sort`` allows you to explicitly set the order in which
  you would like the encoding to appear
- passing a :class:`EncodingSortField` class to ``sort`` allows you to sort
  an axis by the value of some other field in the dataset.

Here is an example of applying these five different sort approaches on the
x-axis, using the barley dataset:

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    barley = data.barley()

    base = alt.Chart(barley).mark_bar().encode(
        y='mean(yield):Q',
        color=alt.Color('mean(yield):Q', legend=None)
    ).properties(width=100, height=100)

    # Sort x in ascending order
    ascending = base.encode(
        alt.X(field='site', type='nominal', sort='ascending')
    ).properties(
        title='Ascending'
    )

    # Sort x in descending order
    descending = base.encode(
        alt.X(field='site', type='nominal', sort='descending')
    ).properties(
        title='Descending'
    )

    # Sort x in an explicitly-specified order
    explicit = base.encode(
        alt.X(field='site', type='nominal',
              sort=['Duluth', 'Grand Rapids', 'Morris',
                    'University Farm', 'Waseca', 'Crookston'])
    ).properties(
        title='Explicit'
    )

    # Sort according to encoding channel
    sortchannel = base.encode(
        alt.X(field='site', type='nominal',
              sort='y')
    ).properties(
        title='By Channel'
    )

    # Sort according to another field
    sortfield = base.encode(
        alt.X(field='site', type='nominal',
              sort=alt.EncodingSortField(field='yield', op='mean'))
    ).properties(
        title='By Yield'
    )

    alt.concat(
        ascending, descending, explicit,
        sortchannel, sortfield,
        columns=3
    )

The last two charts are the same because the default aggregation 
(see :doc:`transform/aggregate`) is ``mean``. To highlight the 
difference between sorting via channel and sorting via field consider the 
following example where we don't aggregate the data:

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    barley = data.barley()
    base = alt.Chart(barley).mark_point().encode(
        y='yield:Q',
    ).properties(width=200)
    
    # Sort according to encoding channel
    sortchannel = base.encode(
        alt.X(field='site', type='nominal',
              sort='y')
    ).properties(
        title='By Channel'
    )

    # Sort according to another field
    sortfield = base.encode(
        alt.X(field='site', type='nominal',
              sort=alt.EncodingSortField(field='yield', op='min'))
    ).properties(
        title='By Min Yield'
    )
    sortchannel | sortfield

By passing a :class:`EncodingSortField` class to ``sort`` we have more control over 
the sorting process.


Sorting Legends
^^^^^^^^^^^^^^^

While the above examples show sorting of axes by specifying ``sort`` in the
:class:`X` and :class:`Y` encodings, legends can be sorted by specifying
``sort`` in the :class:`Color` encoding:

.. altair-plot::

    alt.Chart(barley).mark_rect().encode(
        alt.X('mean(yield):Q', sort='ascending'),
        alt.Y('site:N', sort='descending'),
        alt.Color('site:N',
            sort=['Morris', 'Duluth', 'Grand Rapids',
                  'University Farm', 'Waseca', 'Crookston']
        )
    )

Here the y-axis is sorted reverse-alphabetically, while the color legend is
sorted in the specified order, beginning with ``'Morris'``.
