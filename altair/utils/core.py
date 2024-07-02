"""
Utility routines
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from copy import deepcopy
import json
import itertools
import re
import sys
import traceback
import warnings
from typing import (
    Callable,
    TypeVar,
    Any,
    Iterator,
    cast,
    Literal,
    Protocol,
    TYPE_CHECKING,
    runtime_checkable,
)
from itertools import groupby
from operator import itemgetter

import jsonschema
import narwhals as nw
from narwhals.dependencies import is_pandas_dataframe as _is_pandas_dataframe
import numpy as np

from altair.utils.schemapi import SchemaBase, Undefined

if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec


if TYPE_CHECKING:
    from types import ModuleType
    import typing as t
    from altair.vegalite.v5.schema._typing import StandardType_T as InferredVegaLiteType
    from altair.utils._dfi_types import DataFrame as DfiDataFrame
    from altair.utils.data import DataType
    from narwhals.typing import IntoExpr
    import pandas as pd

V = TypeVar("V")
P = ParamSpec("P")


@runtime_checkable
class DataFrameLike(Protocol):
    def __dataframe__(
        self, nan_as_null: bool = False, allow_copy: bool = True
    ) -> DfiDataFrame: ...


TYPECODE_MAP = {
    "ordinal": "O",
    "nominal": "N",
    "quantitative": "Q",
    "temporal": "T",
    "geojson": "G",
}

INV_TYPECODE_MAP = {v: k for k, v in TYPECODE_MAP.items()}


# aggregates from vega-lite version 4.6.0
AGGREGATES = [
    "argmax",
    "argmin",
    "average",
    "count",
    "distinct",
    "max",
    "mean",
    "median",
    "min",
    "missing",
    "product",
    "q1",
    "q3",
    "ci0",
    "ci1",
    "stderr",
    "stdev",
    "stdevp",
    "sum",
    "valid",
    "values",
    "variance",
    "variancep",
    "exponential",
    "exponentialb",
]

# window aggregates from vega-lite version 4.6.0
WINDOW_AGGREGATES = [
    "row_number",
    "rank",
    "dense_rank",
    "percent_rank",
    "cume_dist",
    "ntile",
    "lag",
    "lead",
    "first_value",
    "last_value",
    "nth_value",
]

# timeUnits from vega-lite version 4.17.0
TIMEUNITS = [
    "year",
    "quarter",
    "month",
    "week",
    "day",
    "dayofyear",
    "date",
    "hours",
    "minutes",
    "seconds",
    "milliseconds",
    "yearquarter",
    "yearquartermonth",
    "yearmonth",
    "yearmonthdate",
    "yearmonthdatehours",
    "yearmonthdatehoursminutes",
    "yearmonthdatehoursminutesseconds",
    "yearweek",
    "yearweekday",
    "yearweekdayhours",
    "yearweekdayhoursminutes",
    "yearweekdayhoursminutesseconds",
    "yeardayofyear",
    "quartermonth",
    "monthdate",
    "monthdatehours",
    "monthdatehoursminutes",
    "monthdatehoursminutesseconds",
    "weekday",
    "weeksdayhours",
    "weekdayhours",
    "weekdayhoursminutes",
    "weekdayhoursminutesseconds",
    "dayhours",
    "dayhoursminutes",
    "dayhoursminutesseconds",
    "hoursminutes",
    "hoursminutesseconds",
    "minutesseconds",
    "secondsmilliseconds",
    "utcyear",
    "utcquarter",
    "utcmonth",
    "utcweek",
    "utcday",
    "utcdayofyear",
    "utcdate",
    "utchours",
    "utcminutes",
    "utcseconds",
    "utcmilliseconds",
    "utcyearquarter",
    "utcyearquartermonth",
    "utcyearmonth",
    "utcyearmonthdate",
    "utcyearmonthdatehours",
    "utcyearmonthdatehoursminutes",
    "utcyearmonthdatehoursminutesseconds",
    "utcyearweek",
    "utcyearweekday",
    "utcyearweekdayhours",
    "utcyearweekdayhoursminutes",
    "utcyearweekdayhoursminutesseconds",
    "utcyeardayofyear",
    "utcquartermonth",
    "utcmonthdate",
    "utcmonthdatehours",
    "utcmonthdatehoursminutes",
    "utcmonthdatehoursminutesseconds",
    "utcweekday",
    "utcweeksdayhours",
    "utcweekdayhoursminutes",
    "utcweekdayhoursminutesseconds",
    "utcdayhours",
    "utcdayhoursminutes",
    "utcdayhoursminutesseconds",
    "utchoursminutes",
    "utchoursminutesseconds",
    "utcminutesseconds",
    "utcsecondsmilliseconds",
]


def infer_vegalite_type_for_pandas(
    data: object,
) -> InferredVegaLiteType | tuple[InferredVegaLiteType, list[Any]]:
    """
    From an array-like input, infer the correct vega typecode
    ('ordinal', 'nominal', 'quantitative', or 'temporal')

    Parameters
    ----------
    data: object
    """
    # This is safe to import here, as this function is only called on pandas input.
    from pandas.api.types import infer_dtype

    typ = infer_dtype(data, skipna=False)

    if typ in {
        "floating",
        "mixed-integer-float",
        "integer",
        "mixed-integer",
        "complex",
    }:
        return "quantitative"
    elif typ == "categorical" and hasattr(data, "cat") and data.cat.ordered:
        return ("ordinal", data.cat.categories.tolist())
    elif typ in {"string", "bytes", "categorical", "boolean", "mixed", "unicode"}:
        return "nominal"
    elif typ in {
        "datetime",
        "datetime64",
        "timedelta",
        "timedelta64",
        "date",
        "time",
        "period",
    }:
        return "temporal"
    else:
        warnings.warn(
            f"I don't know how to infer vegalite type from '{typ}'.  "
            "Defaulting to nominal.",
            stacklevel=1,
        )
        return "nominal"


def merge_props_geom(feat: dict[str, Any]) -> dict[str, Any]:
    """
    Merge properties with geometry
    * Overwrites 'type' and 'geometry' entries if existing
    """

    geom = {k: feat[k] for k in ("type", "geometry")}
    try:
        feat["properties"].update(geom)
        props_geom = feat["properties"]
    except (AttributeError, KeyError):
        # AttributeError when 'properties' equals None
        # KeyError when 'properties' is non-existing
        props_geom = geom

    return props_geom


def sanitize_geo_interface(geo: t.MutableMapping[Any, Any]) -> dict[str, Any]:
    """Santize a geo_interface to prepare it for serialization.

    * Make a copy
    * Convert type array or _Array to list
    * Convert tuples to lists (using json.loads/dumps)
    * Merge properties with geometry
    """

    geo = deepcopy(geo)

    # convert type _Array or array to list
    for key in geo:
        if str(type(geo[key]).__name__).startswith(("_Array", "array")):
            geo[key] = geo[key].tolist()

    # convert (nested) tuples to lists
    geo_dct: dict = json.loads(json.dumps(geo))

    # sanitize features
    if geo_dct["type"] == "FeatureCollection":
        geo_dct = geo_dct["features"]
        if len(geo_dct) > 0:
            for idx, feat in enumerate(geo_dct):
                geo_dct[idx] = merge_props_geom(feat)
    elif geo_dct["type"] == "Feature":
        geo_dct = merge_props_geom(geo_dct)
    else:
        geo_dct = {"type": "Feature", "geometry": geo_dct}

    return geo_dct


def numpy_is_subtype(dtype: Any, subtype: Any) -> bool:
    try:
        return np.issubdtype(dtype, subtype)
    except (NotImplementedError, TypeError):
        return False


def sanitize_pandas_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize a DataFrame to prepare it for serialization.

    * Make a copy
    * Convert RangeIndex columns to strings
    * Raise ValueError if column names are not strings
    * Raise ValueError if it has a hierarchical index.
    * Convert categoricals to strings.
    * Convert np.bool_ dtypes to Python bool objects
    * Convert np.int dtypes to Python int objects
    * Convert floats to objects and replace NaNs/infs with None.
    * Convert DateTime dtypes into appropriate string representations
    * Convert Nullable integers to objects and replace NaN with None
    * Convert Nullable boolean to objects and replace NaN with None
    * convert dedicated string column to objects and replace NaN with None
    * Raise a ValueError for TimeDelta dtypes
    """
    # This is safe to import here, as this function is only called on pandas input.
    import pandas as pd

    df = df.copy()

    if isinstance(df.columns, pd.RangeIndex):
        df.columns = df.columns.astype(str)

    for col_name in df.columns:
        if not isinstance(col_name, str):
            msg = (
                f"Dataframe contains invalid column name: {col_name!r}. "
                "Column names must be strings"
            )
            raise ValueError(msg)

    if isinstance(df.index, pd.MultiIndex):
        msg = "Hierarchical indices not supported"
        raise ValueError(msg)
    if isinstance(df.columns, pd.MultiIndex):
        msg = "Hierarchical indices not supported"
        raise ValueError(msg)

    def to_list_if_array(val):
        if isinstance(val, np.ndarray):
            return val.tolist()
        else:
            return val

    for dtype_item in df.dtypes.items():
        # We know that the column names are strings from the isinstance check
        # further above but mypy thinks it is of type Hashable and therefore does not
        # let us assign it to the col_name variable which is already of type str.
        col_name = cast(str, dtype_item[0])
        dtype = dtype_item[1]
        dtype_name = str(dtype)
        if dtype_name == "category":
            # Work around bug in to_json for categorical types in older versions
            # of pandas as they do not properly convert NaN values to null in to_json.
            # We can probably remove this part once we require pandas >= 1.0
            col = df[col_name].astype(object)
            df[col_name] = col.where(col.notnull(), None)
        elif dtype_name == "string":
            # dedicated string datatype (since 1.0)
            # https://pandas.pydata.org/pandas-docs/version/1.0.0/whatsnew/v1.0.0.html#dedicated-string-data-type
            col = df[col_name].astype(object)
            df[col_name] = col.where(col.notnull(), None)
        elif dtype_name == "bool":
            # convert numpy bools to objects; np.bool is not JSON serializable
            df[col_name] = df[col_name].astype(object)
        elif dtype_name == "boolean":
            # dedicated boolean datatype (since 1.0)
            # https://pandas.io/docs/user_guide/boolean.html
            col = df[col_name].astype(object)
            df[col_name] = col.where(col.notnull(), None)
        elif dtype_name.startswith(("datetime", "timestamp")):
            # Convert datetimes to strings. This needs to be a full ISO string
            # with time, which is why we cannot use ``col.astype(str)``.
            # This is because Javascript parses date-only times in UTC, but
            # parses full ISO-8601 dates as local time, and dates in Vega and
            # Vega-Lite are displayed in local time by default.
            # (see https://github.com/vega/altair/issues/1027)
            df[col_name] = (
                df[col_name].apply(lambda x: x.isoformat()).replace("NaT", "")
            )
        elif dtype_name.startswith("timedelta"):
            msg = (
                f'Field "{col_name}" has type "{dtype}" which is '
                "not supported by Altair. Please convert to "
                "either a timestamp or a numerical value."
                ""
            )
            raise ValueError(msg)
        elif dtype_name.startswith("geometry"):
            # geopandas >=0.6.1 uses the dtype geometry. Continue here
            # otherwise it will give an error on np.issubdtype(dtype, np.integer)
            continue
        elif (
            dtype_name
            in {
                "Int8",
                "Int16",
                "Int32",
                "Int64",
                "UInt8",
                "UInt16",
                "UInt32",
                "UInt64",
                "Float32",
                "Float64",
            }
        ):  # nullable integer datatypes (since 24.0) and nullable float datatypes (since 1.2.0)
            # https://pandas.pydata.org/pandas-docs/version/0.25/whatsnew/v0.24.0.html#optional-integer-na-support
            col = df[col_name].astype(object)
            df[col_name] = col.where(col.notnull(), None)
        elif numpy_is_subtype(dtype, np.integer):
            # convert integers to objects; np.int is not JSON serializable
            df[col_name] = df[col_name].astype(object)
        elif numpy_is_subtype(dtype, np.floating):
            # For floats, convert to Python float: np.float is not JSON serializable
            # Also convert NaN/inf values to null, as they are not JSON serializable
            col = df[col_name]
            bad_values = col.isnull() | np.isinf(col)
            df[col_name] = col.astype(object).where(~bad_values, None)
        elif dtype == object:  # noqa: E721
            # Convert numpy arrays saved as objects to lists
            # Arrays are not JSON serializable
            col = df[col_name].astype(object).apply(to_list_if_array)
            df[col_name] = col.where(col.notnull(), None)
    return df


def sanitize_narwhals_dataframe(data: nw.DataFrame) -> nw.DataFrame:
    """Sanitize narwhals.DataFrame for JSON serialization"""
    schema = data.schema
    columns: list[IntoExpr] = []
    for name, dtype in schema.items():
        if dtype == nw.Date:
            columns.append(nw.col(name).dt.to_string("%Y-%m-%d"))
        elif dtype == nw.Datetime:
            columns.append(nw.col(name).dt.to_string("%Y-%m-%dT%H:%M:%S%.f"))
        elif dtype == nw.Duration:
            msg = (
                f'Field "{name}" has type "{dtype}" which is '
                "not supported by Altair. Please convert to "
                "either a timestamp or a numerical value."
                ""
            )
            raise ValueError(msg)
        else:
            columns.append(name)
    return data.select(columns)


def narwhalify(data: DataType) -> nw.DataFrame:
    """Wrap `data` in `narwhals.DataFrame`.

    If `data` is not supported by Narwhals, but it is convertible
    to a PyArrow table, then first convert to a PyArrow Table,
    and then wrap in `narwhals.DataFrame`.
    """
    data = nw.from_native(data, eager_only=True, strict=False)
    if isinstance(data, nw.DataFrame):
        return data
    if isinstance(data, DataFrameLike):
        from altair.utils.data import arrow_table_from_dfi_dataframe

        pa_table = arrow_table_from_dfi_dataframe(data)
        return nw.from_native(pa_table, eager_only=True)
    msg = f"Unsupported data type: {type(data)}"
    raise TypeError(msg)


def parse_shorthand(
    shorthand: dict[str, Any] | str,
    data: pd.DataFrame | DataFrameLike | None = None,
    parse_aggregates: bool = True,
    parse_window_ops: bool = False,
    parse_timeunits: bool = True,
    parse_types: bool = True,
) -> dict[str, Any]:
    """General tool to parse shorthand values

    These are of the form:

    - "col_name"
    - "col_name:O"
    - "average(col_name)"
    - "average(col_name):O"

    Optionally, a dataframe may be supplied, from which the type
    will be inferred if not specified in the shorthand.

    Parameters
    ----------
    shorthand : dict or string
        The shorthand representation to be parsed
    data : DataFrame, optional
        If specified and of type DataFrame, then use these values to infer the
        column type if not provided by the shorthand.
    parse_aggregates : boolean
        If True (default), then parse aggregate functions within the shorthand.
    parse_window_ops : boolean
        If True then parse window operations within the shorthand (default:False)
    parse_timeunits : boolean
        If True (default), then parse timeUnits from within the shorthand
    parse_types : boolean
        If True (default), then parse typecodes within the shorthand

    Returns
    -------
    attrs : dict
        a dictionary of attributes extracted from the shorthand

    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({'foo': ['A', 'B', 'A', 'B'],
    ...                      'bar': [1, 2, 3, 4]})

    >>> parse_shorthand('name') == {'field': 'name'}
    True

    >>> parse_shorthand('name:Q') == {'field': 'name', 'type': 'quantitative'}
    True

    >>> parse_shorthand('average(col)') == {'aggregate': 'average', 'field': 'col'}
    True

    >>> parse_shorthand('foo:O') == {'field': 'foo', 'type': 'ordinal'}
    True

    >>> parse_shorthand('min(foo):Q') == {'aggregate': 'min', 'field': 'foo', 'type': 'quantitative'}
    True

    >>> parse_shorthand('month(col)') == {'field': 'col', 'timeUnit': 'month', 'type': 'temporal'}
    True

    >>> parse_shorthand('year(col):O') == {'field': 'col', 'timeUnit': 'year', 'type': 'ordinal'}
    True

    >>> parse_shorthand('foo', data) == {'field': 'foo', 'type': 'nominal'}
    True

    >>> parse_shorthand('bar', data) == {'field': 'bar', 'type': 'quantitative'}
    True

    >>> parse_shorthand('bar:O', data) == {'field': 'bar', 'type': 'ordinal'}
    True

    >>> parse_shorthand('sum(bar)', data) == {'aggregate': 'sum', 'field': 'bar', 'type': 'quantitative'}
    True

    >>> parse_shorthand('count()', data) == {'aggregate': 'count', 'type': 'quantitative'}
    True
    """
    from altair.utils.data import is_data_type

    if not shorthand:
        return {}

    valid_typecodes = list(TYPECODE_MAP) + list(INV_TYPECODE_MAP)

    units = {
        "field": "(?P<field>.*)",
        "type": "(?P<type>{})".format("|".join(valid_typecodes)),
        "agg_count": "(?P<aggregate>count)",
        "op_count": "(?P<op>count)",
        "aggregate": "(?P<aggregate>{})".format("|".join(AGGREGATES)),
        "window_op": "(?P<op>{})".format("|".join(AGGREGATES + WINDOW_AGGREGATES)),
        "timeUnit": "(?P<timeUnit>{})".format("|".join(TIMEUNITS)),
    }

    patterns = []

    if parse_aggregates:
        patterns.extend([r"{agg_count}\(\)"])
        patterns.extend([r"{aggregate}\({field}\)"])
    if parse_window_ops:
        patterns.extend([r"{op_count}\(\)"])
        patterns.extend([r"{window_op}\({field}\)"])
    if parse_timeunits:
        patterns.extend([r"{timeUnit}\({field}\)"])

    patterns.extend([r"{field}"])

    if parse_types:
        patterns = list(itertools.chain(*((p + ":{type}", p) for p in patterns)))

    regexps = (
        re.compile(r"\A" + p.format(**units) + r"\Z", re.DOTALL) for p in patterns
    )

    # find matches depending on valid fields passed
    if isinstance(shorthand, dict):
        attrs = shorthand
    else:
        attrs = next(
            exp.match(shorthand).groupdict()  # type: ignore[union-attr]
            for exp in regexps
            if exp.match(shorthand) is not None
        )

    # Handle short form of the type expression
    if "type" in attrs:
        attrs["type"] = INV_TYPECODE_MAP.get(attrs["type"], attrs["type"])

    # counts are quantitative by default
    if attrs == {"aggregate": "count"}:
        attrs["type"] = "quantitative"

    # times are temporal by default
    if "timeUnit" in attrs and "type" not in attrs:
        attrs["type"] = "temporal"

    # if data is specified and type is not, infer type from data
    if "type" not in attrs and is_data_type(data):
        data_nw = narwhalify(data)
        unescaped_field = attrs["field"].replace("\\", "")
        if isinstance(data_nw, nw.DataFrame) and unescaped_field in data_nw.columns:
            column = data_nw[unescaped_field]
            if column.dtype in {nw.Object, nw.Unknown} and _is_pandas_dataframe(data):
                attrs["type"] = infer_vegalite_type_for_pandas(nw.to_native(column))
            else:
                attrs["type"] = infer_vegalite_type_for_narwhals(column)
            if isinstance(attrs["type"], tuple):
                attrs["sort"] = attrs["type"][1]
                attrs["type"] = attrs["type"][0]

    # If an unescaped colon is still present, it's often due to an incorrect data type specification
    # but could also be due to using a column name with ":" in it.
    if (
        "field" in attrs
        and ":" in attrs["field"]
        and attrs["field"][attrs["field"].rfind(":") - 1] != "\\"
    ):
        raise ValueError(
            '"{}" '.format(attrs["field"].split(":")[-1])
            + "is not one of the valid encoding data types: {}.".format(
                ", ".join(TYPECODE_MAP.values())
            )
            + "\nFor more details, see https://altair-viz.github.io/user_guide/encodings/index.html#encoding-data-types. "
            + "If you are trying to use a column name that contains a colon, "
            + 'prefix it with a backslash; for example "column\\:name" instead of "column:name".'
        )
    return attrs


def infer_vegalite_type_for_narwhals(
    column: nw.Series,
) -> InferredVegaLiteType | tuple[InferredVegaLiteType, list]:
    dtype = column.dtype
    if nw.is_ordered_categorical(column):
        return "ordinal", column.cat.get_categories().to_list()
    if dtype in {nw.String, nw.Categorical, nw.Boolean}:
        return "nominal"
    elif dtype.is_numeric():
        return "quantitative"
    elif dtype in {nw.Datetime, nw.Date}:
        return "temporal"
    else:
        msg = f"Unexpected DtypeKind: {dtype}"
        raise ValueError(msg)


def use_signature(Obj: Callable[P, Any]):  # -> Callable[..., Callable[P, V]]:
    """Apply call signature and documentation of Obj to the decorated method"""

    def decorate(f: Callable[..., V]) -> Callable[P, V]:
        # call-signature of f is exposed via __wrapped__.
        # we want it to mimic Obj.__init__
        f.__wrapped__ = Obj.__init__  # type: ignore
        f._uses_signature = Obj  # type: ignore

        # Supplement the docstring of f with information from Obj
        if Obj.__doc__:
            # Patch in a reference to the class this docstring is copied from,
            # to generate a hyperlink.
            doclines = Obj.__doc__.splitlines()
            doclines[0] = f"Refer to :class:`{Obj.__name__}`"

            if f.__doc__:
                doc = f.__doc__ + "\n".join(doclines[1:])
            else:
                doc = "\n".join(doclines)
            f.__doc__ = doc

        return f

    return decorate


def update_nested(
    original: t.MutableMapping[Any, Any],
    update: t.Mapping[Any, Any],
    copy: bool = False,
) -> t.MutableMapping[Any, Any]:
    """Update nested dictionaries

    Parameters
    ----------
    original : MutableMapping
        the original (nested) dictionary, which will be updated in-place
    update : Mapping
        the nested dictionary of updates
    copy : bool, default False
        if True, then copy the original dictionary rather than modifying it

    Returns
    -------
    original : MutableMapping
        a reference to the (modified) original dict

    Examples
    --------
    >>> original = {'x': {'b': 2, 'c': 4}}
    >>> update = {'x': {'b': 5, 'd': 6}, 'y': 40}
    >>> update_nested(original, update)  # doctest: +SKIP
    {'x': {'b': 5, 'c': 4, 'd': 6}, 'y': 40}
    >>> original  # doctest: +SKIP
    {'x': {'b': 5, 'c': 4, 'd': 6}, 'y': 40}
    """
    if copy:
        original = deepcopy(original)
    for key, val in update.items():
        if isinstance(val, Mapping):
            orig_val = original.get(key, {})
            if isinstance(orig_val, MutableMapping):
                original[key] = update_nested(orig_val, val)
            else:
                original[key] = val
        else:
            original[key] = val
    return original


def display_traceback(in_ipython: bool = True):
    exc_info = sys.exc_info()

    if in_ipython:
        from IPython.core.getipython import get_ipython

        ip = get_ipython()
    else:
        ip = None

    if ip is not None:
        ip.showtraceback(exc_info)
    else:
        traceback.print_exception(*exc_info)


_ChannelType = Literal["field", "datum", "value"]
_CHANNEL_CACHE: _ChannelCache
"""Singleton `_ChannelCache` instance.

Initialized on first use.
"""


class _ChannelCache:
    channel_to_name: dict[type[SchemaBase], str]
    name_to_channel: dict[str, dict[_ChannelType, type[SchemaBase]]]

    @classmethod
    def from_channels(cls, channels: ModuleType, /) -> _ChannelCache:
        # - This branch is only kept for tests that depend on mocking `channels`.
        # - No longer needs to pass around `channels` reference and rebuild every call.
        c_to_n = {
            c: c._encoding_name
            for c in channels.__dict__.values()
            if isinstance(c, type)
            and issubclass(c, SchemaBase)
            and hasattr(c, "_encoding_name")
        }
        self = cls.__new__(cls)
        self.channel_to_name = c_to_n
        self.name_to_channel = _invert_group_channels(c_to_n)
        return self

    @classmethod
    def from_cache(cls) -> _ChannelCache:
        global _CHANNEL_CACHE
        try:
            cached = _CHANNEL_CACHE
        except NameError:
            cached = cls.__new__(cls)
            cached.channel_to_name = _init_channel_to_name()
            cached.name_to_channel = _invert_group_channels(cached.channel_to_name)
            _CHANNEL_CACHE = cached
        return _CHANNEL_CACHE

    def get_encoding(self, tp: type[Any], /) -> str:
        if encoding := self.channel_to_name.get(tp):
            return encoding
        msg = f"positional of type {type(tp).__name__!r}"
        raise NotImplementedError(msg)

    def _wrap_in_channel(self, obj: Any, encoding: str, /):
        if isinstance(obj, SchemaBase):
            return obj
        elif isinstance(obj, str):
            obj = {"shorthand": obj}
        elif isinstance(obj, (list, tuple)):
            return [self._wrap_in_channel(el, encoding) for el in obj]
        if channel := self.name_to_channel.get(encoding):
            tp = channel["value" if "value" in obj else "field"]
            try:
                # Don't force validation here; some objects won't be valid until
                # they're created in the context of a chart.
                return tp.from_dict(obj, validate=False)
            except jsonschema.ValidationError:
                # our attempts at finding the correct class have failed
                return obj
        else:
            warnings.warn(f"Unrecognized encoding channel {encoding!r}", stacklevel=1)
            return obj

    def infer_encoding_types(self, kwargs: dict[str, Any], /):
        return {
            encoding: self._wrap_in_channel(obj, encoding)
            for encoding, obj in kwargs.items()
            if obj is not Undefined
        }


def _init_channel_to_name():
    """
    Construct a dictionary of channel type to encoding name.

    Note
    ----
    The return type is not expressible using annotations, but is used
    internally by `mypy`/`pyright` and avoids the need for type ignores.

    Returns
    -------
        mapping: dict[type[`<subclass of FieldChannelMixin and SchemaBase>`] | type[`<subclass of ValueChannelMixin and SchemaBase>`] | type[`<subclass of DatumChannelMixin and SchemaBase>`], str]
    """
    from altair.vegalite.v5.schema import channels as ch

    mixins = ch.FieldChannelMixin, ch.ValueChannelMixin, ch.DatumChannelMixin

    return {
        c: c._encoding_name
        for c in ch.__dict__.values()
        if isinstance(c, type) and issubclass(c, mixins) and issubclass(c, SchemaBase)
    }


def _invert_group_channels(
    m: dict[type[SchemaBase], str], /
) -> dict[str, dict[_ChannelType, type[SchemaBase]]]:
    """Grouped inverted index for `_ChannelCache.channel_to_name`."""

    def _reduce(it: Iterator[tuple[type[Any], str]]) -> Any:
        """Returns a 1-2 item dict, per channel.

        Never includes `datum`, as it is never utilized in `wrap_in_channel`.
        """
        item: dict[Any, type[SchemaBase]] = {}
        for tp, _ in it:
            name = tp.__name__
            if name.endswith("Datum"):
                continue
            elif name.endswith("Value"):
                sub_key = "value"
            else:
                sub_key = "field"
            item[sub_key] = tp
        return item

    grouper = groupby(m.items(), itemgetter(1))
    return {k: _reduce(chans) for k, chans in grouper}


def infer_encoding_types(
    args: tuple[Any, ...], kwargs: dict[str, Any], channels: ModuleType | None = None
):
    """Infer typed keyword arguments for args and kwargs

    Parameters
    ----------
    args : Sequence
        Sequence of function args
    kwargs : MutableMapping
        Dict of function kwargs
    channels : ModuleType
        The module containing all altair encoding channel classes.

    Returns
    -------
    kwargs : dict
        All args and kwargs in a single dict, with keys and types
        based on the channels mapping.
    """
    cache = (
        _ChannelCache.from_channels(channels)
        if channels
        else _ChannelCache.from_cache()
    )
    # First use the mapping to convert args to kwargs based on their types.
    for arg in args:
        el = next(iter(arg), None) if isinstance(arg, (list, tuple)) else arg
        encoding = cache.get_encoding(type(el))
        if encoding not in kwargs:
            kwargs[encoding] = arg
        else:
            msg = f"encoding {encoding!r} specified twice."
            raise ValueError(msg)

    return cache.infer_encoding_types(kwargs)
