.. _changes:

Release Notes
=============

Version 5.3.0 (unreleased month day, year)
--------------------------
- Update Vega-Lite from version 5.16.3 to version 5.17.0;
  see `Vega-Lite Release Notes <https://github.com/vega/vega-lite/releases>`_.

Enhancements
~~~~~~~~~~~~
- Add "jupyter" renderer which uses JupyterChart for rendering (#3283). See :ref:`renderers` for more information.
- Add integration of VegaFusion and JupyterChart to support data transformations in the Python kernel for interactive charts (##3281). See :ref:`vegafusion-data-transformer` for more information.
- Add ``embed_options`` argument to JupyterChart to allow customization of Vega Embed options (#3304)
- Add offline support for JupyterChart and the new "jupyter" renderer. See :ref:`user-guide-jupyterchart-offline`
  for more information.
- Add ``"browser"`` renderer to support displaying Altair charts in an external web browser.
  See :ref:`display-browser` for more information (#3379).
- Docs: Add :ref:`section on dashboards <display_dashboards>` which have support for Altair (#3299)
- Support restrictive FIPS-compliant environment (#3291)
- Support opening charts in the Vega editor with ``chart.open_editor()`` (#3358)
- Simplify type-hints to improve the readability of the function signature and docstring (#3307)
- Support installation of all optional dependencies via ``python -m pip install altair[all]`` (#3354)
    - ``conda install altair-all`` will be added in `this conda feedstock PR <https://github.com/conda-forge/altair-feedstock/pull/53>`_)
- Add privacy friendly web-analytics for the documentation (#3350)
- Additional gallery examples and documentation clarifications (#3233, #3266, #3276, #3282, #3298, #3299, #3323, #3334, #3324, #3340, #3350, #3353, #3357, #3362, #3363) 

Bug Fixes
~~~~~~~~~
- Fix error when embed_options are None (#3376)
- Fix type hints for libraries such as Polars where Altair uses the dataframe interchange protocol (#3297)
- Fix anywidget deprecation warning (#3364)
- Fix handling of Date32 columns in arrow tables and Polars DataFrames (#3377)

Backward-Incompatible Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Updated ``chart.show()`` method to invoke the active renderer rather than depend on ``altair_saver`` (Which was never updated for use with Altair 5) (#3379).
- Changed hash function from ``md5`` to a truncated ``sha256`` non-cryptograhic hash (#3291)

Version 5.2.0 (released Nov 28, 2023)
-------------------------------------------
- Update Vega-Lite from version 5.15.1 to version 5.16.3;
  see `Vega-Lite Release Notes <https://github.com/vega/vega-lite/releases>`_.

Enhancements
~~~~~~~~~~~~
- Support offline HTML export using vl-convert (#3251)
- Support saving charts as PDF files using the vl-convert export engine (#3244)
- Support converting charts to sharable Vega editor URLs with ``chart.to_url()`` (#3252)
- Pass `formatLocale` and `timeFormatLocale` through to vl-convert to support locales in static image export (#3274)
- Vega-Altair is now a typed package, with type annotations for all public functions and classes and some of the internal code (#2951)

Maintenance
~~~~~~~~~~~

- Vega-Altair now uses ``ruff`` for maintaining code quality & consistency (#3243)
- Vega-Altair is tested against Python 3.12 (#3235)

Bug Fixes
~~~~~~~~~

Backward-Incompatible Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Version 5.1.2 (released Oct 3, 2023)
----------------------------------------

- Update Vega-Lite from version 5.14.1 to version 5.15.1;
  see `Vega-Lite 5.15.1 Release Notes <https://github.com/vega/vega-lite/releases/tag/v5.15.1>`_.

Bug Fixes
~~~~~~~~~
- Remove usage of deprecated pandas parameter ``convert_dtypes`` (#3191)
- Fix encoding type inference for boolean columns when pyarrow is installed (#3210)

Version 5.1.1 (released August 30, 2023)
----------------------------------------

Bug Fixes
~~~~~~~~~
- Fall back to type inference logic of the pandas-based implementation to infer object data types (#3179)

Version 5.1.0 (released August 28, 2023)
----------------------------------------

- Update Vega-Lite from version 5.8.0 to version 5.14.1;
  see `Vega-Lite 5.14.1 Release Notes <https://github.com/vega/vega-lite/releases/tag/v5.14.1>`_.

Enhancements
~~~~~~~~~~~~
- Add ``chart.transformed_data()`` method to extract transformed chart data using VegaFusion (#3081, #3084, #3102)
- Add ``"vegafusion"`` data transformer with mime renderer, save, and ``to_dict``/``to_json`` integration (#3094, #3107)
- Add ``JupyterChart`` to support accessing params and selections from Python (See :ref:`user-guide-jupyterchart`)  (#3151)
- Support field encoding inference for objects that support the DataFrame Interchange Protocol (#3114)
- Support grouped bars inside time axis with time bins (see `Vega-Lite 5.9.0 Release Notes <https://github.com/vega/vega-lite/releases/tag/v5.9.0>`_)
- Add new transform method `transform_extent` (#3148)
- Add support for new referencing logic in version 4.18 of the jsonschema package
- Add configurable pixels-per-inch (ppi) metadata to saved and displayed PNG images (#3163)

Bug Fixes
~~~~~~~~~
- Don't call ``len`` on DataFrame Interchange Protocol objects (#3111)

Backward-Incompatible Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Drop support for Python 3.7 which is end-of-life (#3100)
- Hard dependencies: Increase minimum required pandas version to 0.25 (#3130)
- Soft dependencies: Increase minimum required vl-convert-python version to 0.13.0 and increase minimum required vegafusion version to 1.4.0 (#3163, #3160)

Version 5.0.1 (released May 26, 2023)
-------------------------------------

- Remove unwanted files during build to avoid littering site-packages folder (#3057).
- Deprecate the ``.ref()`` function for selections, instead of removing it (#3063).
- Fix bug in reconstructing layered charts with ``Chart.from_json()``/``Chart.from_dict()`` (#3068).

Version 5.0.0 (released May 9, 2023)
------------------------------------

- Update Vega-Lite from version 4.17.0 to version 5.8.0;
  see `Vega-Lite 5.8.0 Release Notes <https://github.com/vega/vega-lite/releases/tag/v5.8.0>`_.

Enhancements
~~~~~~~~~~~~

- As described in the release notes for `Vega-Lite 5.0.0 <https://github.com/vega/vega-lite/releases/tag/v5.0.0>`_, the primary change in this release of Altair is the introduction of parameters. There are two types of parameters, selection parameters and variable parameters.  Variable parameters are new to Altair, and while selections are not new, much of the old terminology has been deprecated.  See :ref:`gallery_slider_cutoff` for an application of variable parameters (#2528).
- Grouped bar charts and jitter are now supported using offset channels, see :ref:`gallery_grouped_bar_chart2` and :ref:`gallery_strip_plot_jitter`
- `vl-convert <https://github.com/vega/vl-convert>`_ is now used as the default backend for saving Altair charts as svg and png files, which simplifies saving chart as it does not require external dependencies like `altair_saver <http://github.com/altair-viz/altair_saver>`_ does (#2701). Currently, `altair_saver <http://github.com/altair-viz/altair_saver>`_ does not support Altair 5 and it is recommended to switch to `vl-convert <https://github.com/vega/vl-convert>`_. See :ref:`saving-png` for more details.
- Saving charts with HTML inline is now supported without having `altair_saver <http://github.com/altair-viz/altair_saver>`_ installed (#2807).
- The default chart width was changed from 400 to 300 (#2785).
- Ordered pandas categorical data are now automatically encoded as sorted ordinal data (#2522)
- The ``Title`` and ``Impute`` aliases were added for ``TitleParams`` and ``ImputeParams``, respectively (#2732).
- The documentation page has been revamped, both in terms of appearance and content.
- More informative autocompletion by removing deprecated methods (#2814) and for editors that rely on type hints (e.g. VS Code) we added support for completion in method chains (#2846) and extended keyword completion to cover additional methods (#2920).
- Substantially improved error handling. Both in terms of finding the more relevant error (#2842), and in terms of improving the formatting and clarity of the error messages (#2824, #2568, #2979, #3009).
- Include experimental support for the DataFrame Interchange Protocol (through ``__dataframe__`` attribute). This requires ``pyarrow>=11.0.0`` (#2888).
- Support data type inference for columns with special characters (#2905).
- Responsive width support using ``width="container"`` when saving charts to html or displaying them with the default  `html` renderer (#2867).

Grammar Changes
~~~~~~~~~~~~~~~

- Channel options can now be set via a more convenient method-based syntax in addition to the previous attribute-based syntax. For example, instead of ``alt.X(..., bin=alt.Bin(...))`` it is now recommend to use ``alt.X(...).bin(...)```) (#2795). See :ref:`method-based-attribute-setting` for details.
- ``selection_single`` and ``selection_multi`` are now deprecated; use ``selection_point`` instead.  Similarly, ``type=point`` should be used instead of ``type=single`` and ``type=multi``.
- ``add_selection`` is deprecated; use ``add_params`` instead.
- The ``selection`` keyword argument must in many cases be replaced by ``param`` (e.g., when specifying a filter transform).
- The ``empty`` keyword argument for a selection parameter should be specified as ``True`` or ``False`` instead of ``all`` or ``none``, respectively.
- The ``init`` keyword argument for a parameter is deprecated; use ``value`` instead.

Bug Fixes
~~~~~~~~~

- Displaying a chart not longer changes the shorthand syntax of the stored spec (#2813).
- Fixed ``disable_debug_mode`` (#2851).
- Fixed issue where the webdriver was not working with Firefox's geckodriver (#2466).
- Dynamically determine the jsonschema validator to avoid issues with recent jsonschema versions (#2812).

Backward-Incompatible Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Colons in column names must now be escaped to remove any ambiguity with encoding types. You now need to write ``"column\:name"`` instead of ``"column:name"`` (#2824).
- Removed the Vega (v5) wrappers and deprecate rendering in Vega mode (save Chart as Vega format is still allowed) (#2829).
- Removed the Vega-Lite 3 and 4 wrappers (#2847).
- Removed the deprecated datasets.py (#3010).
- In regards to the grammar changes listed above, the old terminology will still work in many basic cases.  On the other hand, if that old terminology gets used at a lower level, then it most likely will not work.  For example, in the current version of :ref:`gallery_scatter_with_minimap`, two instances of the key ``param`` are used in dictionaries to specify axis domains.  Those used to be ``selection``, but that usage is not compatible with the current Vega-Lite schema.
- Removed the ``altair.sphinxext`` module (#2792). The ``altair-plot`` Sphinx directive is now part of the `sphinxext-altair <https://github.com/altair-viz/sphinxext-altair>`_ package.

Maintenance
~~~~~~~~~~~

- Vega-Altair now uses ``hatch`` for package management.
- Vega-Altair now uses ``ruff`` for linting.

Version 4.2.2 (released Jan 27, 2023)
-------------------------------------

Bug Fixes
~~~~~~~~~

- Fix incompatibility with jsonschema < 4.5 which got introduced in Altair 4.2.1 (#2860).

Version 4.2.1 (released Jan 26, 2023)
-------------------------------------

Bug Fixes
~~~~~~~~~

- Disable uri-reference format check in jsonsschema (#2771).
- Replace ``iteritems`` with ``items`` due to pandas deprecation (#2683).

Maintenance
~~~~~~~~~~~

- Add deprecation and removal warnings for Vega-Lite v3 wrappers and Vega v5 wrappers (#2843).

Version 4.2.0 (released Dec 29, 2021)
-------------------------------------

- Update Vega-Lite from version 4.8.1 to version 4.17.0;
  see `Vega-Lite 4.17.0 Release Notes <https://github.com/vega/vega-lite/releases/tag/v4.17.0>`_.

Enhancements
~~~~~~~~~~~~

- Pie charts are now supported through the use of ``mark_arc``. (Examples: eg.
  :ref:`gallery_pie_chart` and :ref:`gallery_radial_chart`.)
- Support for the ``datum`` encoding specifications from Vega-Lite; see
  `Vega-Lite Datum Definition <https://vega.github.io/vega-lite/docs/encoding.html#datum-def>`_.
  (Examples: :ref:`gallery_line_chart_with_datum` and :ref:`gallery_line_chart_with_color_datum`.)
- ``angle`` encoding can now be used to control point styles (Example: :ref:`gallery_wind_vector_map`)
- Support for serialising pandas nullable data types for float data (#2399).
- Automatically create an empty data object when ``Chart`` is called without a data parameter (#2515).
- Allow the use of pathlib Paths when saving charts (#2355).
- Support deepcopy for charts (#2403).

Bug Fixes
~~~~~~~~~

- Fix ``to_dict()`` for nested selections (#2120).
- Fix item access for expressions (#2099).

Version 4.1.0 (released April 1, 2020)
--------------------------------------

- Minimum Python version is now 3.6
- Update Vega-Lite to version 4.8.1; many new features and bug fixes from Vega-Lite
  versions 4.1 through 4.8; see `Vega-Lite 4.8.0 Release Notes <https://github.com/vega/vega-lite/releases/tag/v4.8.0>`_.

Enhancements
~~~~~~~~~~~~

- ``strokeDash`` encoding can now be used to control line styles (Example:
  `Multi Series Line Chart <https://altair-viz.github.io/gallery/multi_series_line.html>`_)
- ``chart.save()`` now relies on `altair_saver <http://github.com/altair-viz/altair_saver>`_
  for more flexibility (#1943).
- New ``chart.show()`` method replaces ``chart.serve()``, and relies on
  `altair_viewer <http://github.com/altair-viz/altair_viewer>`_ to allow offline
  viewing of charts (#1988).

Bug Fixes
~~~~~~~~~

- Support Python 3.8 (#1958)
- Support multiple views in JupyterLab (#1986)
- Support numpy types within specifications (#1914)
- Support pandas nullable ints and string types (#1924)

Maintenance
~~~~~~~~~~~

- Altair now uses `black <https://github.com/psf/black>`_ and
  `flake8 <https://gitlab.com/pycqa/flake8>`_ for maintaining code quality & consistency.

Version 4.0.1 (released Jan 14, 2020)
-------------------------------------

Bug Fixes
~~~~~~~~~

- Update Vega-Lite version to 4.0.2
- Fix issue with duplicate chart divs in HTML renderer (#1888)

Version 4.0.0 (released Dec 10, 2019)
-------------------------------------

Version 4.0.0 is based on Vega-Lite version 4.0, which you can read about at
https://github.com/vega/vega-lite/releases/tag/v4.0.0.

It is the first version of Altair to drop Python 2 compatibility, and is tested
on Python 3.5 and newer.

Enhancements
~~~~~~~~~~~~

- Support for interactive legends: (see :ref:`gallery_interactive_legend`)

- Responsive chart width and height: (see :ref:`customization-chart-size`)

- Lookup transform responsive to selections: (see :ref:`user-guide-lookup-transform`)

- Bins responsive to selections: (see :ref:`gallery_histogram_responsive`)

- New Regression transform: (see :ref:`user-guide-regression-transform`)

- New LOESS transform: (see :ref:`user-guide-loess-transform`)

- New density transform: (see :ref:`user-guide-density-transform`)

- New pivot transform: (see :ref:`user-guide-pivot-transform`)

- Image mark (see :ref:`user-guide-image-marks`)

- New default ``html`` renderer, directly compatible with Jupyter Notebook and
  JupyterLab without the need for frontend extensions, as well as tools like
  nbviewer and nbconvert, and related notebook environments such as Zeppelin,
  Colab, Kaggle Kernels, and DataBricks. To enable the old default renderer, use::

      alt.renderers.enable('mimetype')

- Support per-corner radius for bar marks: (see :ref:`gallery_bar_rounded`)

Grammar Changes
~~~~~~~~~~~~~~~

- Sort-by-field can now use the field name directly. So instead of::

      alt.Y('y:Q', sort=alt.EncodingSortField('x', order='descending'))

  you can now use::

      alt.Y('y:Q', sort="-x")

- The ``rangeStep`` argument to :class:`Scale` and :meth:`Chart.configure_scale` is deprecated.
  instead, use ``chart.properties(width={"step": rangeStep})`` or
  ``chart.configure_view(step=rangeStep)``.

- ``align``, ``center``, ``spacing``, and ``columns`` are no longer valid chart properties, but
  are moved to the encoding classes to which they refer.


Version 3.3.0 (released Nov 27, 2019)
-------------------------------------

Last release to support Python 2

Enhancements
~~~~~~~~~~~~

-  Add inheritance structure to low-level schema classes (#1803)
-  Add ``html`` renderer which works across frontends (#1793)
-  Support Python 3.8 (#1740, #1781)
-  Add ``:G`` shorthand for geojson type (#1714)
-  Add data generator interface: ``alt.sequence``, ``alt.graticule``,
   ``alt.sphere()`` (#1667, #1687)
-  Support geographic data sources via ``__geo_interface__`` (#1664)

Bug Fixes
~~~~~~~~~

-  Support ``pickle`` and ``copy.deepcopy`` for chart objects (#1805)
-  Fix bug when specifying ``count()`` within
   ``transform_joinaggregate()`` (#1751)
-  Fix ``LayerChart.add_selection`` (#1794)
-  Fix arguments to ``project()`` method (#1717)
-  Fix composition of multiple selections (#1707)

Version 3.2.0 (released August 5, 2019)
---------------------------------------

Upgraded to Vega-Lite version 3.4 (See `Vega-Lite 3.4 Release
Notes <https://github.com/vega/vega-lite/releases/tag/v3.4.0>`__).

Following are changes to Altair in addition to those that came with VL
3.4:

Enhancements
~~~~~~~~~~~~

-  Selector values can be used directly in expressions (#1599)
-  Top-level chart repr is now truncated to improve readability of error
   messages (#1572)

Bug Fixes
~~~~~~~~~

-  top-level ``add_selection`` methods now delegate to sub-charts.
   Previously they produced invalid charts (#1607)
-  Unsupported ``mark_*()`` methods removed from LayerChart (#1607)
-  New encoding channels are properly parsed (#1597)
-  Data context is propagated when encodings are specified as lists
   (#1587)

Backward-Incompatible Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``alt.LayerChart`` no longer has ``mark_*()`` methods, because they
   never produced valid chart specifications) (#1607)

Version 3.1.0 (Released June 6, 2019)
-------------------------------------

Update includes full compatibility with version 3.3 of Vega-Lite.

Enhancements
~~~~~~~~~~~~

-  Added support for `vega
   themes <https://github.com/vega/vega-themes>`__ via
   ``alt.themes.enable(theme_name)`` (#1539)

-  Added an ``alt.renderers.disable_max_rows()`` method for disabling
   the maximum rows check (#1538)

-  Improved user-facing warnings/errors around layering and faceting
   (#1535).

-  ``data`` argument is now properly handled by ``Chart.properties``
   (#1525)

-  Compound charts (layer, concat, hconcat, vconcat) now move data to
   the top level by default. In particular, this means that the
   ``facet()`` method can now be called directly on a layered chart
   without having to change how data is specified. (#1521)

-  ``alt.LayerChart`` now supports ``mark_*()`` methods. If a layer
   specifies a mark at the top level, all child charts will inherit it
   (unless they override it explicitly).

-  ``alt.Chart.facet()`` now handles wrapped facets; for example:
   ``python   chart.facet('column_name', columns=5)`` See
   ``altair/examples/us_population_over_time_facet.py`` for a more
   complete example.

Bug fixes
~~~~~~~~~

-  Make ``chart.serve()`` and ``chart.save()`` respect the data
   transformer setting (#1538)

-  Fixed a deserialization bug for certain chart specs in schemapi
   (#1543)

Backward-Incompatible Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``alt.Chart.facet()`` now accepts a wrapped facet encoding as a first
   positional argument, rather than a row encoding. The following are
   examples of old invocations, and the equivalent new invocations:

-  ``chart.facet(row='col1', column='col2')``: unchanged
-  ``chart.facet('col1', 'col2')``: change to
   ``chart.facet(row='col1', column='col2')``
-  ``chart.facet('col1')``: change to ``chart.facet(row='col1')``

In each case, the new invocations are compatible back to Altair 2.X.

-  Several of the encoding channels added in 3.0 have had their
   capitalization corrected to better match the names used in the
   schema:

-  ``alt.Fillopacity`` -> ``alt.FillOpacity``
-  ``alt.Strokeopacity`` -> ``alt.StrokeOpacity``
-  ``alt.Strokewidth`` -> ``alt.StrokeWidth``
-  ``alt.Xerror`` -> ``alt.XError``
-  ``alt.Xerror2`` -> ``alt.XError2``
-  ``alt.Yerror`` -> ``alt.YError``
-  ``alt.Yerror2`` -> ``alt.YError2``

Version 3.0.1 (Released May 1, 2019)
------------------------------------

Fix version info bug for HTML output and Colab & Kaggle renderers.

Version 3.0.0 (Released April 26, 2019)
---------------------------------------

Update to Vega-Lite 3.2 and Vega 5.3 & support all new features. See
https://github.com/vega/vega-lite/releases/tag/v3.0.0 for Vega-Lite
feature lists.

Highlights:
~~~~~~~~~~~

-  new compound marks: ``mark_boxplot()``, ``mark_errorband()``,
   ``mark_errorbar()``
-  new transforms: ``transform_impute()``,
   ``transform_joinaggregate()``, ``transform_flatten()``
   ``transform_fold()``, ``transform_sample()``, ``transform_stack()``
-  new ``facet`` encoding that is similar to the ``row`` and ``column``
   encoding, but allows for wrapped facets
-  new ``alt.concat()`` function that is similar to ``alt.hconcat`` and
   ``alt.vconcat``, but allows for more general wrapped concatenation
-  new ``columns`` keyword that allows wrapped faceting, repeating, and
   concatenation.
-  many, many bug fixes
-  tooltips can now be automatically populated using the ``tooltip``
   mark configuration.
-  ability to specify initial conditions for selections

Version 2.4.1 (Released February 21, 2019)
------------------------------------------

Enhancements
~~~~~~~~~~~~

-  Several documentation cleanups & new examples

Bug Fixes
~~~~~~~~~

-  Fix incompatibility with pandas version 0.24 (#1315)

Version 2.3.0 (Released December 7, 2018)
-----------------------------------------

Includes many reworked examples in the example gallery.

Enhancements
~~~~~~~~~~~~

-  Better errors for non-string column names, as well as automatic
   conversion of ``pandas.RangeIndex`` columns to strings (#1107)

-  Renderers now have set\_embed\_options() method (#1203)

-  Added kaggle renderer & more HTML output options (#1123)

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Maintenance
~~~~~~~~~~~

-  fix typing requirement in Python 3.6+ (#1185)

-  Added support & CI testing for Python 3.7 (#1008)

Bug fixes
~~~~~~~~~

-  Selection predicates now recognize all valid entries (#1143)
-  Python 2 support for ``chart.save()`` (#1134)

Version 2.2.2 (Released August 17, 2018)
----------------------------------------

Bug Fixes
~~~~~~~~~

-  fix missing JSON resource in ``altair.vega.v4`` (#1097)

Version 2.2.1 (Released August 15, 2018)
----------------------------------------

Bug Fixes
~~~~~~~~~

-  appropriate handling of InlineData in dataset consolidation (#1092)

-  fix admonition formatting in documentation page (#1094)

Version 2.2.0 (Released August 14, 2018):
-----------------------------------------

Enhancements
~~~~~~~~~~~~

-  better handling of datetimes and timezones (#1053)

-  all inline datasets are now converted to named datasets and stored at
   the top level of the chart. This behavior can be disabled by setting
   ``alt.data_transformers.consolidate_datasets = False`` (#951 & #1046)

-  more streamlined shorthand syntax for window transforms (#957)

Maintenance
~~~~~~~~~~~

-  update from Vega-Lite 2.4.3 to Vega-Lite 2.6.0; see vega-lite
   change-logs
   `2.5.0 <https://github.com/vega/vega-lite/releases/tag/v2.5.0>`__
   `2.5.1 <https://github.com/vega/vega-lite/releases/tag/v2.5.1>`__
   `2.5.2 <https://github.com/vega/vega-lite/releases/tag/v2.5.2>`__
   `2.6.0 <https://github.com/vega/vega-lite/releases/tag/v2.6.0>`__

Backward-incompatible changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  ``alt.SortField`` renamed to ``alt.EncodingSortField`` and
   ``alt.WindowSortField`` renamed to ``alt.SortField`` (#3741)

Bug Fixes
~~~~~~~~~

-  Fixed serialization of logical operands on selections within
   ``transform_filter()``: (#1075)

-  Fixed sphinx issue which embedded chart specs twice (#1088)

-  Avoid Selenium import until it is actually needed (#982)

Version 2.1.0 (Released June 6, 2018):
--------------------------------------

Enhancements
~~~~~~~~~~~~

-  add a ``scale_factor`` argument to ``chart.save()`` to allow the
   size/resolution of saved figures to be adjusted. (#918)

-  add an ``add_selection()`` method to add selections to charts (#832)

-  add ``chart.serve()`` and ``chart.display()`` methods for more
   flexibility in displaying charts (#831)

-  allow multiple fields to be passed to encodings such as ``tooltip``
   and ``detail`` (#830)

-  make ``timeUnit`` specifications more succinct, by parsing them in a
   manner similar to aggregates (#866)

-  make ``to_json()`` and ``to_csv()`` have deterministic filenames, so
   in json mode a single datasets will lead to a single on-disk
   serialization (#862)

Breaking Changes
~~~~~~~~~~~~~~~~

-  make ``data`` the first argument for all compound chart types to
   match the semantics of ``alt.Chart`` (this includes
   ``alt.FacetChart``, ``alt.LayerChart``, ``alt.RepeatChart``,
   ``alt.VConcatChart``, and ``alt.HConcatChart``) (#895).

-  update vega-lite to version 2.4.3 (#836)

-  Only API change is internal: ``alt.MarkProperties`` is now
   ``alt.MarkConfig``

Maintenance
~~~~~~~~~~~

-  update vega to v3.3 & vega-embed to v3.11 in html output & colab
   renderer (#838)

Version 2.0.0: May 2, 2018
--------------------------

-  Complete rewrite of Altair, focused on supporting Vega-Lite 2.X

Version 1.2.1: October 29, 2017
-------------------------------

This version of Altair is based on Vega-Lite 1.2.1.

Major additions
~~~~~~~~~~~~~~~

-  Support for JupyterLab/nteract through MIME based rendering. Enable
   this by calling ``enable_mime_rendering()`` before rendering
   visualizations
   (`#216 <https://github.com/altair-viz/altair/pull/216>`__).

-  Change default import in all code and docs to
   ``import altair as alt``

-  Check for missing and misspelled column names upon exporting or
   rendering, and raise ``FieldError``
   (`#399 <https://github.com/altair-viz/altair/pull/399>`__) if any
   problems are found. This can be disabled by setting
   ``Chart.validated_columns=False``.

-  Raise ``MaxRowsExceeded`` if the number of rows in the dataset is
   larger than ``Chart.max_rows`` to guard against sending large
   datasets to the browser.

-  Move the Vega-Lite 1.x api into ``altair.v1`` to make it easier for
   us to migrate to Vega-Lite 2.x and continue to support 1.x. No import
   change are needed as ``altair.v1`` is aliased to ``altair`` in this
   release\ ``altair.v1``
   (`#377 <https://github.com/altair-viz/altair/pull/377>`__).

-  Moved the example notebooks into a separate repository
   (https://github.com/altair-viz/altair\_notebooks) that has Binder
   support (`#391 <https://github.com/altair-viz/altair/pull/391>`__).

-  Add ``$schema`` to top-level JSON spec
   (`#370 <https://github.com/altair-viz/altair/issues/370>`__).

-  Minor documentation revisions.

Bug fixes
~~~~~~~~~

-  Make sure default mark is a point
   (`#344 <https://github.com/altair-viz/altair/pull/344>`__).

Version 1.2: Nov 7, 2016
------------------------

Major additions
~~~~~~~~~~~~~~~

-  Update to Vega-Lite 1.2 and make all its enhancements available to
   Altair

-  Add ``Chart.serve`` method
   (`#197 <https://github.com/altair-viz/altair/pull/197>`__)

-  Add ``altair.expr`` machinery to specify transformations and
   filterings (`#215 <https://github.com/altair-viz/altair/pull/215>`__)

-  Add ``Chart.savechart`` method, which can output JSON, HTML, and (if
   Node is installed) PNG and SVG. See
   https://altair-viz.github.io/documentation/displaying.html
   (`#213 <https://github.com/altair-viz/altair/pull/213>`__)

Bug fixes
~~~~~~~~~

-  Countless minor bug fixes

maintenance:
~~~~~~~~~~~~

-  Update to Vega-Lite 1.2.1 and add its supported features

-  Create website: http://altair-viz.github.io/

-  Set up Travis to run conda & pip; and to build documentation

Version 1.0: July 11, 2016
--------------------------

-  Initial release of Altair
