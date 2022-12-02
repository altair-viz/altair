.. currentmodule:: altair

.. _user-guide-aggregate-transform:

Aggregate
~~~~~~~~~
There are two ways to aggregate data within Altair: within the encoding itself,
or using a top level aggregate transform.

The aggregate property of a field definition can be used to compute aggregate
summary statistics (e.g., :code:`median`, :code:`min`, :code:`max`) over groups of data.

If at least one fields in the specified encoding channels contain aggregate,
the resulting visualization will show aggregate data. In this case, all
fields without aggregation function specified are treated as group-by fields
in the aggregation process.

For example, the following bar chart aggregates mean of ``acceleration``,
grouped by the number of Cylinders.

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    cars = data.cars.url

    alt.Chart(cars).mark_bar().encode(
        y='Cylinders:O',
        x='mean(Acceleration):Q'
    )

The Altair shorthand string::

    # ...
    x='mean(Acceleration):Q',
    # ...

is made available for convenience, and is equivalent to the longer form::

    # ...
    x=alt.X(field='Acceleration', aggregate='mean', type='quantitative'),
    # ...

For more information on shorthand encodings specifications, see
:ref:`shorthand-description`.

The same plot can be shown via an explicitly computed aggregation, using the
:meth:`~Chart.transform_aggregate` method:

.. altair-plot::

    alt.Chart(cars).mark_bar().encode(
        y='Cylinders:O',
        x='mean_acc:Q'
    ).transform_aggregate(
        mean_acc='mean(Acceleration)',
        groupby=["Cylinders"]
    )

The alternative to using aggregate functions is to preprocess the data with
Pandas, and then plot the resulting DataFrame:

.. altair-plot::

   cars_df = data.cars()
   source = (
      cars_df.groupby('Cylinders')
      .Acceleration
      .mean()
      .reset_index()
      .rename(columns={'Acceleration': 'mean_acc'})
   )

   alt.Chart(source).mark_bar().encode(
      y='Cylinders:O',
      x='mean_acc:Q'
   )

**Note:** As mentioned in :doc:`../data`, this approach of transforming the
data with Pandas is preferable if we already have the DataFrame at hand.

Because :code:`Cylinders` is of type :code:`int64` in the :code:`source`
DataFrame, Altair would have treated it as a :code:`qualitative` --instead of
:code:`ordinal`-- type, had we not specified it. Making the type of data
explicit is important since it affects the resulting plot; see
:ref:`type-legend-scale` and :ref:`type-axis-scale` for two illustrated
examples. As a rule of thumb, it is better to make the data type explicit,
instead of relying on an implicit type conversion.

Functions Without Arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is possible for aggregate functions to not
have an argument. In this case, aggregation will be performed on the column
used in the other axis.

The following chart demonstrates this by counting the number of cars with
respect to their country of origin.

.. altair-plot::

   alt.Chart(cars).mark_bar().encode(
      y='Origin:N',
      # shorthand form of alt.Y(aggregate='count')
      x='count()'
   )

**Note:** The :code:`count` aggregate function is of type
:code:`quantitative` by default, it does not matter if the source data is a
DataFrame, URL pointer, CSV file or JSON file.

Functions that handle categorical data (such as :code:`count`,
:code:`missing`, :code:`distinct` and :code:`valid`) are the ones that get
the most out of this feature.

Argmin / Argmax
^^^^^^^^^^^^^^^
Both :code:`argmin` and :code:`argmax` aggregate functions can only be used
with the :meth:`~Chart.transform_aggregate` method. Trying to use their
respective shorthand notations will result in an error. This is due to the fact
that either :code:`argmin` or :code:`argmax` functions return an object, not
values.  This object then specifies the values to be selected from other
columns when encoding.  One can think of the returned object as being a
dictionary, while the column serves the purpose of being a key, which then
obtains its respective value.

The true value of these functions is appreciated when we want to compare the
most **distinctive** samples from two sets of data with respect to another set
of data.

As an example, suppose we want to compare the weight of the strongest cars,
with respect to their country/region of origin. This can be done using
:code:`argmax`:

.. altair-plot::

   alt.Chart(cars).mark_bar().encode(
      x='greatest_hp[Weight_in_lbs]:Q',
      y='Origin:N'
   ).transform_aggregate(
      greatest_hp='argmax(Horsepower)',
      groupby=['Origin']
   )

It is clear that Japan's strongest car is also the lightest, while that of USA
is the heaviest.

See :ref:`gallery_line_chart_with_custom_legend` for another example that uses
:code:`argmax`. The case of :code:`argmin` is completely similar.

Transform Options
^^^^^^^^^^^^^^^^^
The :meth:`~Chart.transform_aggregate` method is built on the :class:`~AggregateTransform`
class, which has the following options:

.. altair-object-table:: altair.AggregateTransform

The :class:`~AggregatedFieldDef` objects have the following options:

.. altair-object-table:: altair.AggregatedFieldDef

.. _agg-func-table:

List of Aggregation Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to ``count`` and ``average``, there are a large number of available
aggregation functions built into Altair; they are listed in the following table:

=========  ===========================================================================  =====================================
Aggregate  Description                                                                  Example
=========  ===========================================================================  =====================================
argmin     An input data object containing the minimum field value.                     N/A
argmax     An input data object containing the maximum field value.                     :ref:`gallery_line_chart_with_custom_legend`
average    The mean (average) field value. Identical to mean.                           :ref:`gallery_layer_line_color_rule`
count      The total count of data objects in the group.                                :ref:`gallery_simple_heatmap`
distinct   The count of distinct field values.                                          N/A
max        The maximum field value.                                                     :ref:`gallery_boxplot`
mean       The mean (average) field value.                                              :ref:`gallery_scatter_with_layered_histogram`
median     The median field value                                                       :ref:`gallery_boxplot`
min        The minimum field value.                                                     :ref:`gallery_boxplot`
missing    The count of null or undefined field values.                                 N/A
q1         The lower quartile boundary of values.                                       :ref:`gallery_boxplot`
q3         The upper quartile boundary of values.                                       :ref:`gallery_boxplot`
ci0        The lower boundary of the bootstrapped 95% confidence interval of the mean.  :ref:`gallery_sorted_error_bars_with_ci`
ci1        The upper boundary of the bootstrapped 95% confidence interval of the mean.  :ref:`gallery_sorted_error_bars_with_ci`
stderr     The standard error of the field values.                                      N/A
stdev      The sample standard deviation of field values.                               N/A
stdevp     The population standard deviation of field values.                           N/A
sum        The sum of field values.                                                     :ref:`gallery_streamgraph`
product    The product of field values.                                                 N/A
valid      The count of field values that are not null or undefined.                    N/A
values     ??                                                                           N/A
variance   The sample variance of field values.                                         N/A
variancep  The population variance of field values.                                     N/A
=========  ===========================================================================  =====================================
