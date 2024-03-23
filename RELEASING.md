1. Create a new virtual environment following the instructions in `CONTRIBUTING.md`.
   Make sure to also install all dependencies for the documentation.

2. Make certain your branch is in sync with head:
 
       git pull upstream main

3. Do a clean doc build:

       hatch run doc:clean-all
       hatch run doc:build-html
       hatch run doc:serve
   
   Navigate to http://localhost:8000 and ensure it looks OK (particularly
   do a visual scan of the gallery thumbnails).

4. Make sure changes.rst is up to date for the release: compare against PRs
   merged since the last release & update top heading with release date.

5. Update version to, e.g. 5.0.0:

   - in ``altair/__init__.py``
   - in ``doc/conf.py``

6. Double-check that all vega-lite/vega/vega-embed versions are up-to-date:

   - URLs in ``doc/conf.py``
   - versions in ``altair/vegalite/v5/display.py``

7. Commit change and push to main:

       git add . -u
       git commit -m "MAINT: bump version to 5.0.0"
       git push upstream main

8. Tag the release:

       git tag -a v5.0.0 -m "version 5.0.0 release"
       git push upstream v5.0.0

9. Build source & wheel distributions:

       hatch clean  # clean old builds & distributions
       hatch build  # create a source distribution and universal wheel

10. publish to PyPI (Requires correct PyPI owner permissions):

        hatch publish

11. build and publish docs (Requires write-access to altair-viz/altair-viz.github.io):

        hatch run doc:publish-clean-build

12. update version to, e.g. 5.1.0dev:

    - in ``altair/__init__.py``
    - in ``doc/conf.py``

12. Commit change and push to main:

        git add . -u
        git commit -m "MAINT: bump version to 5.1.0dev"
        git push upstream main

13. Double-check that a conda-forge pull request is generated from the updated
    pip package by the conda-forge bot (may take up to ~an hour):
    https://github.com/conda-forge/altair-feedstock/pulls

14. Publish a new release in https://github.com/altair-viz/altair/releases/

**Temporary until we have released Version 5.3.0**. Here some draft release notes.

Version 5.3.0 (unreleased month day, year)
--------------------------
- Update Vega-Lite from version 5.16.3 to version 5.17.0;
  see `Vega-Lite Release Notes <https://github.com/vega/vega-lite/releases>`_.

Enhancements
~~~~~~~~~~~~
- Add "jupyter" renderer which uses JupyterChart for rendering (#3283). See :ref:`renderers` for more information.
- Add integration of VegaFusion and JupyterChart to support data transformations in the Python kernel for interactive charts (##3281). See :ref:`vegafusion-data-transformer` for more information.
- Add ``embed_options`` argument to JupyterChart to allow customization of Vega Embed options (##3304)
- Add offline support for JupyterChart and the new "jupyter" renderer. See :ref:`user-guide-jupyterchart-offline`
  for more information.
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

Backward-Incompatible Changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- Changed hash function from ``md5`` to a truncated ``sha256`` non-cryptograhic hash (#3291)

