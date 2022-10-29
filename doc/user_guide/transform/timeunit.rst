.. currentmodule:: altair

.. _user-guide-timeunit-transform:

TimeUnit Transform
~~~~~~~~~~~~~~~~~~
TimeUnit transforms are used to discretize dates and times within Altair.
As with the :ref:`user-guide-aggregate-transform` and :ref:`user-guide-bin-transform`
discussed above, they can be defined either as part of the encoding, or as a
top-level transform.

These are the available time units:

- ``"year"``, ``"yearquarter"``, ``"yearquartermonth"``, ``"yearmonth"``,
  ``"yearmonthdate"``, ``"yearmonthdatehours"``, ``"yearmonthdatehoursminutes"``,
  ``"yearmonthdatehoursminutesseconds"``.
- ``"quarter"``, ``"quartermonth"``
- ``"month"``, ``"monthdate"``
- ``"date"`` (Day of month, i.e., 1 - 31)
- ``"day"`` (Day of week, i.e., Monday - Friday)
- ``"hours"``, ``"hoursminutes"``, ``"hoursminutesseconds"``
- ``"minutes"``, ``"minutesseconds"``
- ``"seconds"``, ``"secondsmilliseconds"``
- ``"milliseconds"``

TimeUnit Within Encoding
^^^^^^^^^^^^^^^^^^^^^^^^
Any temporal field definition can include a ``timeUnit`` argument to discretize
the temporal data.

For example, here we plot a dataset that consists of hourly temperature
measurements in Seattle during the year 2010:

.. altair-plot::

    import altair as alt
    from vega_datasets import data

    temps = data.seattle_weather_hourly_normals.url

    alt.Chart(temps).mark_line().encode(
        x='date:T',
        y='temperature:Q'
    )

The plot is too busy due to the amount of data points squeezed into the short
time; we can make it a bit cleaner by discretizing it, for example, by month
and plotting only the mean monthly temperature:

.. altair-plot::

    alt.Chart(temps).mark_line().encode(
        x='month(date):T',
        y='mean(temperature):Q'
    )

Notice that by default timeUnit output is a continuous quantity; if you would
instead like it to be a categorical, you can specify the ordinal (``O``) or
nominal (``N``) type.
This can be useful when plotting a bar chart or other discrete chart type:

.. altair-plot::

    alt.Chart(temps).mark_bar().encode(
        x='month(date):O',
        y='mean(temperature):Q'
    )

Multiple time units can be combined within a single plot to yield interesting
views of your data; for example, here we extract both the month and the day
to give a profile of Seattle temperatures through the year:

.. altair-plot::

    alt.Chart(temps).mark_rect().encode(
        alt.X('date(date):O', title='day'),
        alt.Y('month(date):O', title='month'),
        color='max(temperature):Q'
    ).properties(
        title="2010 Daily High Temperatures in Seattle (F)"
    )

TimeUnit as a Transform
^^^^^^^^^^^^^^^^^^^^^^^
Other times it is convenient to specify a timeUnit as a top-level transform,
particularly when the value may be reused.
This can be done most conveniently using the :meth:`Chart.transform_timeunit`
method. For example:

.. altair-plot::

    alt.Chart(temps).mark_line().encode(
        alt.X('month:T', axis=alt.Axis(format='%b')),
        y='mean(temperature):Q'
    ).transform_timeunit(
        month='month(date)'
    )

Notice that because the ``timeUnit`` is not part of the encoding channel here,
it is often necessary to add an axis formatter to ensure appropriate axis
labels.

Transform Options
^^^^^^^^^^^^^^^^^
The :meth:`~Chart.transform_timeunit` method is built on the :class:`~TimeUnitTransform`
class, which has the following options:

.. altair-object-table:: altair.TimeUnitTransform
