.. currentmodule:: altair

.. _user-guide-time:

Times and Dates in Altair
=========================
Working with dates, times, and timezones is often one of the more challenging
aspects of data analysis. In Altair, the difficulties are compounded by the
fact that users are writing Python code, which outputs JSON-serialized
timestamps, which are interpreted by Javascript, and then rendered by your
browser. At each of these steps, there are things that can go wrong, but
Altair and Vega-Lite do their best to ensure that dates are interpreted and
visualized in a consistent way.


.. _note-browser-compliance:

Note on Browser Compliance
--------------------------

.. note:: Warning about non-ES6 Browsers

   The discussion below applies to modern browsers which support `ECMAScript 6`_,
   in which time strings like ``"2018-01-01T12:00:00"`` without a trailing ``"Z"``
   are treated as local time rather than `Coordinated Universal Time (UTC)`_.
   For example, recent versions of Chrome and Firefox are ES6-compliant,
   while Safari 11 is not.
   If you are using a non-ES6 browser, this means that times displayed in Altair
   charts may be rendered with a timezone offset, unless you explicitly use
   UTC time (see :ref:`explicit-utc-time`).

The following chart will help you determine if your browser parses dates in the
way that Altair expects:

.. altair-plot::
    :links: none

    import altair as alt
    import pandas as pd

    df = pd.DataFrame({'local': ['2018-01-01T00:00:00'],
                       'utc': ['2018-01-01T00:00:00Z']})

    alt.Chart(df).transform_calculate(
        compliant="hours(datum.local) != hours(datum.utc) ? true : false",
    ).mark_text(size=20, baseline='middle').encode(
        text=alt.condition('datum.compliant', alt.value('OK'), alt.value('not OK')),
        color=alt.condition('datum.compliant', alt.value('green'), alt.value('red'))
    ).properties(width=80, height=50)

If the above output contains a red "not OK":

.. altair-plot::
   :hide-code:
   :links: none

   alt.Chart(df).mark_text(size=10, baseline='middle').encode(
       alt.TextValue('not OK'),
       alt.ColorValue('red')
   ).properties(width=40, height=25)

it means that your browser's date parsing is not ES6-compliant.
If it contains a green "OK":

.. altair-plot::
   :hide-code:
   :links: none

   alt.Chart(df).mark_text(size=10, baseline='middle').encode(
       alt.TextValue('OK'),
       alt.ColorValue('green')
   ).properties(width=40, height=25)

then it means that your browser parses dates as Altair expects, either because
it is ES6-compliant or because your computer locale happens to be set to
the UTC+0 (GMT) timezone.

Altair and Pandas Datetimes
---------------------------

Altair is designed to work best with `Pandas timeseries`_. A standard
timezone-agnostic date/time column in a Pandas dataframe will be both
interpreted and displayed as local user time. For example, here is a dataset
containing hourly temperatures measured in Seattle:

.. altair-plot::
    :output: repr

    import altair as alt
    from vega_datasets import data

    temps = data.seattle_weather_hourly_normals.url
    temps.head()

We can see from the ``dtypes`` attribute that the times are encoded as a standard
64-bit datetime, without any specified timezone:

.. altair-plot::
    :output: repr

    temps.dtypes

We can use Altair to visualize this datetime data; for clarity in this
example, we'll limit ourselves to the first two weeks of data:

.. altair-plot::

    temps = temps[temps.date < '2010-01-15']

    alt.Chart(temps).mark_line().encode(
        x='date:T',
        y='temperature:Q'
    )

(notice that for date/time values we use the ``T`` to indicate a temporal
encoding: while this is optional for pandas datetime input, it is good practice
to specify a type explicitly; see :ref:`encoding-data-types` for more discussion).

For date-time inputs like these, it can sometimes be useful to extract particular
time units (e.g. hours of the day, dates of the month, etc.).
In Altair, this can be done with a time unit transform, discussed in detail in
:ref:`user-guide-timeunit-transform`.
For example, we might decide we want a heatmap with hour of the day on the
x-axis, and day of the month on the y-axis:

.. altair-plot::

    alt.Chart(temps).mark_rect().encode(
        alt.X('hoursminutes(date):O', title='hour of day'),
        alt.Y('monthdate(date):O', title='date'),
        alt.Color('temperature:Q', title='temperature (F)')
    )

Unless you are using a non-ES6 browser (See :ref:`note-browser-compliance`),
you will notice that the chart created by this code reflects hours starting
at 00:00:00 on January 1st, just as in the data we input.
This is because both the input timestamps and the plot outputs are using
local time.

Specifying Time Zones
---------------------
If you are viewing the above visualizations in a supported browser (see
:ref:`note-browser-compliance` above), the times are both serialized and
rendered in local time, so that the ``January 1st 00:00:00`` row renders in
the chart as ``00:00`` on ``January 1st``.

In Altair, simple dates without an explicit timezone are treated as local time,
and in Vega-Lite, unless otherwise specified, times are rendered in the local
time of the browser that does the rendering.

If you would like your dates to instead be time-zone aware, you can set the
timezone explicitly in the input dataframe. Since Seattle is in the
``US/Pacific`` timezone, we can localize the timestamps in Pandas as follows:

.. altair-plot::
   :output: repr

   temps['date_pacific'] = temps['date'].dt.tz_localize('US/Pacific')
   temps.dtypes

Notice that the timezone is now part of the pandas datatype.
If we repeat the above chart with this timezone-aware data, the result will
render **according to the timezone of the browser rendering it**:

.. altair-plot::

    alt.Chart(temps).mark_rect().encode(
        alt.X('hoursminutes(date_pacific):O', title='hour of day'),
        alt.Y('monthdate(date_pacific):O', title='date'),
        alt.Color('temperature:Q', title='temperature (F)')
    )

If you are viewing this chart on a computer whose time is set to the west coast
of the US, it should appear identical to the first version. If you are rendering
the chart in any other timezone, it will render using a timezone correction
computed from the location set in your system.

.. _explicit-utc-time:

Using UTC Time
--------------
This user-local rendering can sometimes be confusing, because it leads to the
same output being visualized differently by different users.
If you want timezone-aware data to appear the same to every user regardless of
location, the best approach is to adopt a standard timezone in which to render
the data. One commonly-used standard is `Coordinated Universal Time (UTC)`_.
In Altair, any of the ``timeUnit`` bins can be prefixed with ``utc`` in
order to extract UTC time units.

Here is the above chart visualized in UTC time, which will render the same way
regardless of the system location:

.. altair-plot::

    alt.Chart(temps).mark_rect().encode(
        alt.X('utchoursminutes(date_pacific):O', title='UTC hour of day'),
        alt.Y('utcmonthdate(date_pacific):O', title='UTC date'),
        alt.Color('temperature:Q', title='temperature (F)')
    )

To make your charts as portable as possible (even in non-ES6 browsers which parse
timezone-agnostic times as UTC), you can explicitly work
in UTC time, both on the Pandas side and on the Vega-Lite side:


.. altair-plot::

   temps['date_utc'] = temps['date'].dt.tz_localize('UTC')

   alt.Chart(temps).mark_rect().encode(
       alt.X('utchoursminutes(date_utc):O', title='hour of day'),
       alt.Y('utcmonthdate(date_utc):O', title='date'),
       alt.Color('temperature:Q', title='temperature (F)')
   )

This is somewhat less convenient than the default behavior for timezone-agnostic
dates, in which both Pandas and Vega-Lite assume times are local
(except in non-ES6 browsers; see :ref:`note-browser-compliance`),
but it gets around browser incompatibilities by explicitly working in UTC, which
gives similar results even in older browsers.


.. _Coordinated Universal Time (UTC): https://en.wikipedia.org/wiki/Coordinated_Universal_Time
.. _Pandas timeseries: https://pandas.pydata.org/pandas-docs/stable/timeseries.html
.. _ECMAScript 6: http://www.ecma-international.org/ecma-262/6.0/
