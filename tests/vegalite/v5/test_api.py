"""Unit tests for altair API"""

import io
import json
import operator
import os
import pathlib
import tempfile

import jsonschema
import pytest
import pandas as pd

import altair as alt

try:
    import vl_convert as vlc
except ImportError:
    vlc = None


def getargs(*args, **kwargs):
    return args, kwargs


OP_DICT = {
    "layer": operator.add,
    "hconcat": operator.or_,
    "vconcat": operator.and_,
}


def _make_chart_type(chart_type):
    data = pd.DataFrame(
        {
            "x": [28, 55, 43, 91, 81, 53, 19, 87],
            "y": [43, 91, 81, 53, 19, 87, 52, 28],
            "color": list("AAAABBBB"),
        }
    )
    base = (
        alt.Chart(data)
        .mark_point()
        .encode(
            x="x",
            y="y",
            color="color",
        )
    )

    if chart_type in {"layer", "hconcat", "vconcat", "concat"}:
        func = getattr(alt, chart_type)
        return func(base.mark_square(), base.mark_circle())
    elif chart_type == "facet":
        return base.facet("color")
    elif chart_type == "facet_encoding":
        return base.encode(facet="color")
    elif chart_type == "repeat":
        return base.encode(alt.X(alt.repeat(), type="quantitative")).repeat(["x", "y"])
    elif chart_type == "chart":
        return base
    else:
        msg = f"chart_type='{chart_type}' is not recognized"
        raise ValueError(msg)


@pytest.fixture()
def basic_chart():
    data = pd.DataFrame(
        {
            "a": ["A", "B", "C", "D", "E", "F", "G", "H", "I"],
            "b": [28, 55, 43, 91, 81, 53, 19, 87, 52],
        }
    )

    return alt.Chart(data).mark_bar().encode(x="a", y="b")


def test_chart_data_types():
    def Chart(data):
        return alt.Chart(data).mark_point().encode(x="x:Q", y="y:Q")

    # Url Data
    data = "/path/to/my/data.csv"
    dct = Chart(data).to_dict()
    assert dct["data"] == {"url": data}

    # Dict Data
    data = {"values": [{"x": 1, "y": 2}, {"x": 2, "y": 3}]}
    with alt.data_transformers.enable(consolidate_datasets=False):
        dct = Chart(data).to_dict()
    assert dct["data"] == data

    with alt.data_transformers.enable(consolidate_datasets=True):
        dct = Chart(data).to_dict()
    name = dct["data"]["name"]
    assert dct["datasets"][name] == data["values"]

    # DataFrame data
    data = pd.DataFrame({"x": range(5), "y": range(5)})
    with alt.data_transformers.enable(consolidate_datasets=False):
        dct = Chart(data).to_dict()
    assert dct["data"]["values"] == data.to_dict(orient="records")

    with alt.data_transformers.enable(consolidate_datasets=True):
        dct = Chart(data).to_dict()
    name = dct["data"]["name"]
    assert dct["datasets"][name] == data.to_dict(orient="records")

    # Named data object
    data = alt.NamedData(name="Foo")
    dct = Chart(data).to_dict()
    assert dct["data"] == {"name": "Foo"}


@pytest.mark.filterwarnings("ignore:'Y' is deprecated.*:FutureWarning")
def test_chart_infer_types():
    data = pd.DataFrame(
        {
            "x": pd.date_range("2012", periods=10, freq="Y"),
            "y": range(10),
            "c": list("abcabcabca"),
            "s": pd.Categorical([1, 2] * 5, categories=[2, 1], ordered=True),
        }
    )

    def _check_encodings(chart):
        dct = chart.to_dict()
        assert dct["encoding"]["x"]["type"] == "temporal"
        assert dct["encoding"]["x"]["field"] == "x"
        assert dct["encoding"]["y"]["type"] == "quantitative"
        assert dct["encoding"]["y"]["field"] == "y"
        assert dct["encoding"]["color"]["type"] == "nominal"
        assert dct["encoding"]["color"]["field"] == "c"
        assert dct["encoding"]["size"]["type"] == "ordinal"
        assert dct["encoding"]["size"]["field"] == "s"
        assert dct["encoding"]["size"]["sort"] == [2, 1]
        assert dct["encoding"]["tooltip"]["type"] == "ordinal"
        assert dct["encoding"]["tooltip"]["field"] == "s"
        # "sort" should be removed for channels that don't support it
        assert "sort" not in dct["encoding"]["tooltip"]

    # Pass field names by keyword
    chart = (
        alt.Chart(data)
        .mark_point()
        .encode(x="x", y="y", color="c", size="s", tooltip="s")
    )
    _check_encodings(chart)

    # pass Channel objects by keyword
    chart = (
        alt.Chart(data)
        .mark_point()
        .encode(
            x=alt.X("x"),
            y=alt.Y("y"),
            color=alt.Color("c"),
            size=alt.Size("s"),
            tooltip=alt.Tooltip("s"),
        )
    )
    _check_encodings(chart)

    # pass Channel objects by value
    chart = (
        alt.Chart(data)
        .mark_point()
        .encode(alt.X("x"), alt.Y("y"), alt.Color("c"), alt.Size("s"), alt.Tooltip("s"))
    )
    _check_encodings(chart)

    # override default types
    chart = (
        alt.Chart(data)
        .mark_point()
        .encode(
            alt.X("x", type="nominal"),
            alt.Y("y", type="ordinal"),
            alt.Size("s", type="nominal"),
            alt.Tooltip("s", type="nominal"),
        )
    )
    dct = chart.to_dict()
    assert dct["encoding"]["x"]["type"] == "nominal"
    assert dct["encoding"]["y"]["type"] == "ordinal"
    assert dct["encoding"]["size"]["type"] == "nominal"
    assert "sort" not in dct["encoding"]["size"]
    assert dct["encoding"]["tooltip"]["type"] == "nominal"
    assert "sort" not in dct["encoding"]["tooltip"]


@pytest.mark.parametrize(
    ("args", "kwargs"),
    [
        getargs(detail=["value:Q", "name:N"], tooltip=["value:Q", "name:N"]),
        getargs(detail=["value", "name"], tooltip=["value", "name"]),
        getargs(alt.Detail(["value:Q", "name:N"]), alt.Tooltip(["value:Q", "name:N"])),
        getargs(alt.Detail(["value", "name"]), alt.Tooltip(["value", "name"])),
        getargs(
            [alt.Detail("value:Q"), alt.Detail("name:N")],
            [alt.Tooltip("value:Q"), alt.Tooltip("name:N")],
        ),
        getargs(
            [alt.Detail("value"), alt.Detail("name")],
            [alt.Tooltip("value"), alt.Tooltip("name")],
        ),
    ],
)
def test_multiple_encodings(args, kwargs):
    df = pd.DataFrame({"value": [1, 2, 3], "name": ["A", "B", "C"]})
    encoding_dct = [
        {"field": "value", "type": "quantitative"},
        {"field": "name", "type": "nominal"},
    ]
    chart = alt.Chart(df).mark_point().encode(*args, **kwargs)
    dct = chart.to_dict()
    assert dct["encoding"]["detail"] == encoding_dct
    assert dct["encoding"]["tooltip"] == encoding_dct


@pytest.mark.filterwarnings("ignore:'Y' is deprecated.*:FutureWarning")
def test_chart_operations():
    data = pd.DataFrame(
        {
            "x": pd.date_range("2012", periods=10, freq="Y"),
            "y": range(10),
            "c": list("abcabcabca"),
        }
    )
    chart1 = alt.Chart(data).mark_line().encode(x="x", y="y", color="c")
    chart2 = chart1.mark_point()
    chart3 = chart1.mark_circle()
    chart4 = chart1.mark_square()

    chart = chart1 + chart2 + chart3
    assert isinstance(chart, alt.LayerChart)
    assert len(chart.layer) == 3
    chart += chart4
    assert len(chart.layer) == 4

    chart = chart1 | chart2 | chart3
    assert isinstance(chart, alt.HConcatChart)
    assert len(chart.hconcat) == 3
    chart |= chart4
    assert len(chart.hconcat) == 4

    chart = chart1 & chart2 & chart3
    assert isinstance(chart, alt.VConcatChart)
    assert len(chart.vconcat) == 3
    chart &= chart4
    assert len(chart.vconcat) == 4


def test_when() -> None:
    from altair.vegalite.v5 import api as _alt

    select = alt.selection_point(name="select", on="click")
    condition = _alt._predicate_to_condition(select, empty=False)
    when = alt.when(select, empty=False)
    when_constraint = alt.when(Origin="Europe")
    when_constraints = alt.when(
        Name="Name_1", Color="Green", Age=25, StartDate="2000-10-01"
    )
    expected_constraint = alt.datum.Origin == "Europe"
    expected_constraints = (
        (alt.datum.Name == "Name_1")
        & (alt.datum.Color == "Green")
        & (alt.datum.Age == 25)
        & (alt.datum.StartDate == "2000-10-01")
    )

    assert isinstance(when, alt.When)
    assert condition == when._condition
    assert isinstance(when_constraint, alt.When)
    assert when_constraint._condition["test"] == expected_constraint
    assert when_constraints._condition["test"] == expected_constraints
    with pytest.raises((NotImplementedError, TypeError), match="list"):
        alt.when([1, 2, 3])  # type: ignore
    with pytest.raises(TypeError, match="Undefined"):
        alt.when()
    with pytest.raises(TypeError, match="int"):
        alt.when(select, alt.datum.Name == "Name_1", 99, TestCon=5.901)  # type: ignore


def test_when_then() -> None:
    from altair.vegalite.v5 import api as _alt

    select = alt.selection_point(name="select", on="click")
    when = alt.when(select)
    when_then = when.then(alt.value(5))

    assert isinstance(when_then, _alt._Then)
    condition = when_then._conditions["condition"]
    assert isinstance(condition, list)
    assert condition[-1].get("value") == 5

    with pytest.raises(TypeError, match=r"literal.+Path"):
        when.then(pathlib.Path("some"))  # type: ignore

    with pytest.raises(TypeError, match="float"):
        when_then.when(select, alt.datum.Name != "Name_2", 86.123, empty=True)  # type: ignore


def test_when_then_only(basic_chart) -> None:
    """`_Then` is an acceptable encode argument."""

    select = alt.selection_point(name="select", on="click")
    when = alt.when(select)
    when_then = when.then(alt.value(5))

    assert when_then.to_dict() == when.then(5).to_dict()
    basic_chart.encode(fillOpacity=when_then).to_dict()
    with pytest.raises(TypeError, match="list"):
        when.then([5], seq_as_lit=False)  # type: ignore


def test_when_then_otherwise() -> None:
    select = alt.selection_point(name="select", on="click")
    when_then = alt.when(select).then(alt.value(2, empty=False))
    when_then_otherwise = when_then.otherwise(alt.value(0))
    short = alt.when(select).then(2, empty=False).otherwise(0)
    expected = alt.condition(select, alt.value(2, empty=False), alt.value(0))
    when_then.otherwise([1, 2, 3])

    assert when_then_otherwise == short
    # Needed to modify to a list of conditions,
    # which isn't possible in `condition`
    single_condition = expected.pop("condition")
    expected["condition"] = [single_condition]

    assert expected == when_then_otherwise
    with pytest.raises(TypeError, match="list"):
        when_then.otherwise([1, 2, 3], seq_as_lit=False)  # type: ignore


def test_when_then_when_then_otherwise() -> None:
    """Test for [#3301](https://github.com/vega/altair/issues/3301)."""

    data = {
        "values": [
            {"a": "A", "b": 28},
            {"a": "B", "b": 55},
            {"a": "C", "b": 43},
            {"a": "D", "b": 91},
            {"a": "E", "b": 81},
            {"a": "F", "b": 53},
            {"a": "G", "b": 19},
            {"a": "H", "b": 87},
            {"a": "I", "b": 52},
        ]
    }

    select = alt.selection_point(name="select", on="click")
    highlight = alt.selection_point(name="highlight", on="pointerover")
    when_then_when_then = (
        alt.when(select)
        .then(alt.value(2, empty=False))
        .when(highlight)
        .then(alt.value(1, empty=False))
    )
    with pytest.raises(TypeError, match="set"):
        when_then_when_then.otherwise({"five", "six"})  # type: ignore

    actual_stroke = when_then_when_then.otherwise(alt.value(0))
    expected_stroke = {
        "condition": [
            {"param": "select", "empty": False, "value": 2},
            {"param": "highlight", "empty": False, "value": 1},
        ],
        "value": 0,
    }

    assert expected_stroke == actual_stroke
    chart = (
        alt.Chart(data)
        .mark_bar(fill="#4C78A8", stroke="black", cursor="pointer")
        .encode(
            x="a:O",
            y="b:Q",
            fillOpacity=alt.when(select).then(1).otherwise(0.3),  # type: ignore
            strokeWidth=actual_stroke,  # type: ignore
        )
        .configure_scale(bandPaddingInner=0.2)
        .add_params(select, highlight)
    )
    chart.to_dict()


def test_when_labels_position_based_on_condition() -> None:
    """Test for [2144026368-1](https://github.com/vega/altair/pull/3427#issuecomment-2144026368)

    Original [labels-position-based-on-condition](https://altair-viz.github.io/user_guide/marks/text.html#labels-position-based-on-condition)
    """
    import numpy as np
    import pandas as pd
    from altair.utils.schemapi import SchemaValidationError

    from altair.vegalite.v5 import api as _alt

    rand = np.random.RandomState(42)
    df = pd.DataFrame({"xval": range(100), "yval": rand.randn(100).cumsum()})

    bind_range = alt.binding_range(min=100, max=300, name="Slider value:  ")
    param_width = alt.param(bind=bind_range)
    param_width_lt_200 = param_width < 200

    # Examples of how to write both js and python expressions
    param_color_js_expr = alt.param(expr=f"{param_width.name} < 200 ? 'red' : 'black'")
    param_color_py_expr = alt.param(
        expr=alt.expr.if_(param_width_lt_200, "red", "black")
    )
    when = (
        alt.when(param_width_lt_200)
        .then(alt.value("red"))
        .otherwise("black", str_as_lit=True)
    )
    param_color_py_when = alt.param(expr=_alt._condition_to_expr_str(when))
    assert param_color_py_expr.expr == param_color_py_when.expr

    chart = (
        alt.Chart(df)
        .mark_point()
        .encode(
            alt.X("xval").axis(titleColor=param_color_js_expr),
            alt.Y("yval").axis(titleColor=param_color_py_when),
        )
        .add_params(param_width, param_color_js_expr, param_color_py_when)
    )
    chart.to_dict()
    fail_condition = alt.condition(
        param_width < 200, alt.value("red"), alt.value("black")
    )
    with pytest.raises(SchemaValidationError, match="invalid value for `expr`"):
        alt.param(expr=fail_condition)  # type: ignore


def test_when_expressions_inside_parameters() -> None:
    """Test for [2144026368-2](https://github.com/vega/altair/pull/3427#issuecomment-2144026368)

    Original [expressions-inside-parameters](https://altair-viz.github.io/user_guide/interactions.html#expressions-inside-parameters)
    """
    from altair.vegalite.v5 import api as _alt
    import pandas as pd

    source = pd.DataFrame({"a": ["A", "B", "C"], "b": [28, -5, 10]})

    bar = (
        alt.Chart(source)
        .mark_bar()
        .encode(y="a:N", x=alt.X("b:Q").scale(domain=[-10, 35]))
    )
    when_then_otherwise = alt.when(alt.datum.b >= 0).then(10).otherwise(-20)
    expected = alt.expr(alt.expr.if_(alt.datum.b >= 0, 10, -20))
    actual = _alt._condition_to_expr_ref(when_then_otherwise)
    assert expected == actual

    text_conditioned = bar.mark_text(align="left", baseline="middle", dx=actual).encode(
        text="b"
    )

    chart = bar + text_conditioned
    chart.to_dict()


def test_when_convert_expr() -> None:
    from altair.vegalite.v5 import api as _alt

    when = alt.when(Color="Green").then(5).otherwise(10)
    converted = _alt._condition_to_expr_ref(when)

    assert isinstance(converted, alt.ExprRef)

    with pytest.raises(TypeError, match="int"):
        _alt._condition_to_expr_ref(9)  # type: ignore

    with pytest.raises(KeyError, match="Missing `value`"):
        _alt._condition_to_expr_ref(alt.when(Color="Green").then(5).to_dict())

    with pytest.raises(KeyError, match="Missing `condition`"):
        _alt._condition_to_expr_ref({"value": 10})

    with pytest.raises(TypeError, match="'str'"):
        _alt._condition_to_expr_ref({"value": 10, "condition": "words"})  # type: ignore

    with pytest.raises(KeyError, match="Missing `test`"):
        _alt._condition_to_expr_ref(
            alt.when(alt.selection_point("name")).then(33).otherwise(11)
        )

    long = (
        alt.when(Color="red")
        .then(1)
        .when(Color="blue")
        .then(2)
        .when(Color="green")
        .then(3)
        .otherwise(0)
    )

    with pytest.raises(ValueError, match="3"):
        _alt._condition_to_expr_ref(long)


def test_selection_to_dict():
    brush = alt.selection_interval()

    # test some value selections
    # Note: X and Y cannot have conditions
    alt.Chart("path/to/data.json").mark_point().encode(
        color=alt.condition(brush, alt.ColorValue("red"), alt.ColorValue("blue")),
        opacity=alt.condition(brush, alt.value(0.5), alt.value(1.0)),
        text=alt.condition(brush, alt.TextValue("foo"), alt.value("bar")),
    ).to_dict()

    # test some field selections
    # Note: X and Y cannot have conditions
    # Conditions cannot both be fields
    alt.Chart("path/to/data.json").mark_point().encode(
        color=alt.condition(brush, alt.Color("col1:N"), alt.value("blue")),
        opacity=alt.condition(brush, "col1:N", alt.value(0.5)),
        text=alt.condition(brush, alt.value("abc"), alt.Text("col2:N")),
        size=alt.condition(brush, alt.value(20), "col2:N"),
    ).to_dict()


def test_selection_expression():
    from altair.expr.core import Expression

    selection = alt.selection_point(fields=["value"])

    assert isinstance(selection.value, alt.SelectionExpression)
    assert selection.value.to_dict() == {"expr": f"{selection.name}.value"}

    assert isinstance(selection["value"], Expression)
    assert selection["value"].to_dict() == f"{selection.name}['value']"

    magic_attr = "__magic__"
    with pytest.raises(AttributeError):
        getattr(selection, magic_attr)


@pytest.mark.parametrize("format", ["html", "json", "png", "svg", "pdf", "bogus"])
@pytest.mark.parametrize("engine", ["vl-convert"])
def test_save(format, engine, basic_chart):
    if format in {"pdf", "png"}:
        out = io.BytesIO()
        mode = "rb"
    else:
        out = io.StringIO()
        mode = "r"

    if format in {"svg", "png", "pdf", "bogus"} and engine == "vl-convert":
        if format == "bogus":
            with pytest.raises(ValueError) as err:  # noqa: PT011
                basic_chart.save(out, format=format, engine=engine)
            assert f"Unsupported format: '{format}'" in str(err.value)
            return
        elif vlc is None:
            with pytest.raises(ValueError) as err:  # noqa: PT011
                basic_chart.save(out, format=format, engine=engine)
            assert "vl-convert-python" in str(err.value)
            return

    basic_chart.save(out, format=format, engine=engine)
    out.seek(0)
    content = out.read()

    if format == "json":
        assert "$schema" in json.loads(content)
    elif format == "html":
        assert content.startswith("<!DOCTYPE html>")
    elif format == "svg":
        assert content.startswith("<svg")
    elif format == "png":
        assert content.startswith(b"\x89PNG")
    elif format == "pdf":
        assert content.startswith(b"%PDF-")

    fid, filename = tempfile.mkstemp(suffix="." + format)
    os.close(fid)

    # test both string filenames and pathlib.Paths
    for fp in [filename, pathlib.Path(filename)]:
        try:
            basic_chart.save(fp, format=format, engine=engine)
            with pathlib.Path(fp).open(mode) as f:
                assert f.read()[:1000] == content[:1000]
        finally:
            pathlib.Path(fp).unlink()


@pytest.mark.parametrize("inline", [False, True])
def test_save_html(basic_chart, inline):
    if vlc is None:
        pytest.skip("vl_convert not importable; cannot run this test")

    out = io.StringIO()
    basic_chart.save(out, format="html", inline=inline)
    out.seek(0)
    content = out.read()

    assert content.startswith("<!DOCTYPE html>")

    if inline:
        assert '<script type="text/javascript">' in content
    else:
        assert 'src="https://cdn.jsdelivr.net/npm/vega@5' in content
        assert 'src="https://cdn.jsdelivr.net/npm/vega-lite@5' in content
        assert 'src="https://cdn.jsdelivr.net/npm/vega-embed@6' in content


def test_to_url(basic_chart):
    if vlc is None:
        pytest.skip("vl_convert is not installed")

    share_url = basic_chart.to_url()
    expected_vegalite_encoding = "N4Igxg9gdgZglgcxALlANzgUwO4tJKAFzigFcJSBnAdTgBNCALFAZgAY2AacaYsiygAlMiRoVYcAvpO50AhoTl4QUOQFtMKEPMUBaAOwA2ABwAWFi1NyTcgEb7TtuabAswc-XTZhMczLdNDAEYQGRA1OQAnAGtlQgBPAAdNZBAnSNDuTChIOhIkVBAAD2V4TAAbOi0lbgTkrSgINRI5csyQeNKsSq1bEFqklJAAR1I5IjhFYjRNaW4AEkowRkwIrTFCRMpkAHodmYQ5ADoEScZSWyO4CB2llYj9zEPdcsnMfYBWI6D9I7YjgBWlGg-W0CjklEwhEoyh0cgMJnMlmsxjsDicLjcHi8Pj8AWCKAA2qAlKkAIKgvrIABMxhkJK0ACFKSgPh96SBSSAAMIs5DmDlcgAifIAnEFBVoAKJ84wSzgM1IAMT5HxYktSAHE+UFRRqQIJZfp9QBJVXUyQAXWkQA"

    assert (
        share_url
        == f"https://vega.github.io/editor/#/url/vega-lite/{expected_vegalite_encoding}"
    )

    # Check fullscreen
    fullscreen_share_url = basic_chart.to_url(fullscreen=True)
    assert (
        fullscreen_share_url
        == f"https://vega.github.io/editor/#/url/vega-lite/{expected_vegalite_encoding}/view"
    )


def test_facet_basic():
    # wrapped facet
    chart1 = (
        alt.Chart("data.csv")
        .mark_point()
        .encode(
            x="x:Q",
            y="y:Q",
        )
        .facet("category:N", columns=2)
    )

    dct1 = chart1.to_dict()

    assert dct1["facet"] == alt.Facet("category:N").to_dict()
    assert dct1["columns"] == 2
    assert dct1["data"] == alt.UrlData("data.csv").to_dict()

    # explicit row/col facet
    chart2 = (
        alt.Chart("data.csv")
        .mark_point()
        .encode(
            x="x:Q",
            y="y:Q",
        )
        .facet(row="category1:Q", column="category2:Q")
    )

    dct2 = chart2.to_dict()

    assert dct2["facet"]["row"] == alt.Facet("category1:Q").to_dict()
    assert dct2["facet"]["column"] == alt.Facet("category2:Q").to_dict()
    assert "columns" not in dct2
    assert dct2["data"] == alt.UrlData("data.csv").to_dict()


def test_facet_parse():
    chart = (
        alt.Chart("data.csv")
        .mark_point()
        .encode(x="x:Q", y="y:Q")
        .facet(row="row:N", column="column:O")
    )
    dct = chart.to_dict()
    assert dct["data"] == {"url": "data.csv"}
    assert "data" not in dct["spec"]
    assert dct["facet"] == {
        "column": {"field": "column", "type": "ordinal"},
        "row": {"field": "row", "type": "nominal"},
    }


def test_facet_parse_data():
    data = pd.DataFrame({"x": range(5), "y": range(5), "row": list("abcab")})
    chart = (
        alt.Chart(data)
        .mark_point()
        .encode(x="x", y="y:O")
        .facet(row="row", column="column:O")
    )
    with alt.data_transformers.enable(consolidate_datasets=False):
        dct = chart.to_dict()
    assert "values" in dct["data"]
    assert "data" not in dct["spec"]
    assert dct["facet"] == {
        "column": {"field": "column", "type": "ordinal"},
        "row": {"field": "row", "type": "nominal"},
    }

    with alt.data_transformers.enable(consolidate_datasets=True):
        dct = chart.to_dict()
    assert "datasets" in dct
    assert "name" in dct["data"]
    assert "data" not in dct["spec"]
    assert dct["facet"] == {
        "column": {"field": "column", "type": "ordinal"},
        "row": {"field": "row", "type": "nominal"},
    }


def test_selection():
    # test instantiation of selections
    interval = alt.selection_interval(name="selec_1")
    assert interval.param.select.type == "interval"
    assert interval.name == "selec_1"

    single = alt.selection_point(name="selec_2")
    assert single.param.select.type == "point"
    assert single.name == "selec_2"

    multi = alt.selection_point(name="selec_3")
    assert multi.param.select.type == "point"
    assert multi.name == "selec_3"

    # test adding to chart
    chart = alt.Chart().add_params(single)
    chart = chart.add_params(multi, interval)
    assert {x.name for x in chart.params} == {"selec_1", "selec_2", "selec_3"}

    # test logical operations
    assert isinstance(single & multi, alt.SelectionPredicateComposition)
    assert isinstance(single | multi, alt.SelectionPredicateComposition)
    assert isinstance(~single, alt.SelectionPredicateComposition)
    assert "and" in (single & multi).to_dict()
    assert "or" in (single | multi).to_dict()
    assert "not" in (~single).to_dict()

    # test that default names increment (regression for #1454)
    sel1 = alt.selection_point()
    sel2 = alt.selection_point()
    sel3 = alt.selection_interval()
    names = {s.name for s in (sel1, sel2, sel3)}
    assert len(names) == 3


def test_transforms():
    # aggregate transform
    agg1 = alt.AggregatedFieldDef(**{"as": "x1", "op": "mean", "field": "y"})
    agg2 = alt.AggregatedFieldDef(**{"as": "x2", "op": "median", "field": "z"})
    chart = alt.Chart().transform_aggregate([agg1], ["foo"], x2="median(z)")
    kwds = {"aggregate": [agg1, agg2], "groupby": ["foo"]}
    assert chart.transform == [alt.AggregateTransform(**kwds)]

    # bin transform
    chart = alt.Chart().transform_bin("binned", field="field", bin=True)
    kwds = {"as": "binned", "field": "field", "bin": True}
    assert chart.transform == [alt.BinTransform(**kwds)]

    # calcualte transform
    chart = alt.Chart().transform_calculate("calc", "datum.a * 4")
    kwds = {"as": "calc", "calculate": "datum.a * 4"}
    assert chart.transform == [alt.CalculateTransform(**kwds)]

    # density transform
    chart = alt.Chart().transform_density("x", as_=["value", "density"])
    kwds = {"as": ["value", "density"], "density": "x"}
    assert chart.transform == [alt.DensityTransform(**kwds)]

    # extent transform
    chart = alt.Chart().transform_extent("x", "x_extent")
    assert chart.transform == [alt.ExtentTransform(extent="x", param="x_extent")]

    # filter transform
    chart = alt.Chart().transform_filter("datum.a < 4")
    assert chart.transform == [alt.FilterTransform(filter="datum.a < 4")]

    # flatten transform
    chart = alt.Chart().transform_flatten(["A", "B"], ["X", "Y"])
    kwds = {"as": ["X", "Y"], "flatten": ["A", "B"]}
    assert chart.transform == [alt.FlattenTransform(**kwds)]

    # fold transform
    chart = alt.Chart().transform_fold(["A", "B", "C"], as_=["key", "val"])
    kwds = {"as": ["key", "val"], "fold": ["A", "B", "C"]}
    assert chart.transform == [alt.FoldTransform(**kwds)]

    # impute transform
    chart = alt.Chart().transform_impute("field", "key", groupby=["x"])
    kwds = {"impute": "field", "key": "key", "groupby": ["x"]}
    assert chart.transform == [alt.ImputeTransform(**kwds)]

    # joinaggregate transform
    chart = alt.Chart().transform_joinaggregate(min="min(x)", groupby=["key"])
    kwds = {
        "joinaggregate": [
            alt.JoinAggregateFieldDef(field="x", op="min", **{"as": "min"})
        ],
        "groupby": ["key"],
    }
    assert chart.transform == [alt.JoinAggregateTransform(**kwds)]

    # loess transform
    chart = alt.Chart().transform_loess("x", "y", as_=["xx", "yy"])
    kwds = {"on": "x", "loess": "y", "as": ["xx", "yy"]}
    assert chart.transform == [alt.LoessTransform(**kwds)]

    # lookup transform (data)
    lookup_data = alt.LookupData(alt.UrlData("foo.csv"), "id", ["rate"])
    chart = alt.Chart().transform_lookup("a", from_=lookup_data, as_="a", default="b")
    kwds = {"from": lookup_data, "as": "a", "lookup": "a", "default": "b"}
    assert chart.transform == [alt.LookupTransform(**kwds)]

    # lookup transform (selection)
    lookup_selection = alt.LookupSelection(key="key", param="sel")
    chart = alt.Chart().transform_lookup(
        "a", from_=lookup_selection, as_="a", default="b"
    )
    kwds = {"from": lookup_selection, "as": "a", "lookup": "a", "default": "b"}
    assert chart.transform == [alt.LookupTransform(**kwds)]

    # pivot transform
    chart = alt.Chart().transform_pivot("x", "y")
    assert chart.transform == [alt.PivotTransform(pivot="x", value="y")]

    # quantile transform
    chart = alt.Chart().transform_quantile("x", as_=["prob", "value"])
    kwds = {"quantile": "x", "as": ["prob", "value"]}
    assert chart.transform == [alt.QuantileTransform(**kwds)]

    # regression transform
    chart = alt.Chart().transform_regression("x", "y", as_=["xx", "yy"])
    kwds = {"on": "x", "regression": "y", "as": ["xx", "yy"]}
    assert chart.transform == [alt.RegressionTransform(**kwds)]

    # sample transform
    chart = alt.Chart().transform_sample()
    assert chart.transform == [alt.SampleTransform(1000)]

    # stack transform
    chart = alt.Chart().transform_stack("stacked", "x", groupby=["y"])
    assert chart.transform == [
        alt.StackTransform(stack="x", groupby=["y"], **{"as": "stacked"})
    ]

    # timeUnit transform
    chart = alt.Chart().transform_timeunit("foo", field="x", timeUnit="date")
    kwds = {"as": "foo", "field": "x", "timeUnit": "date"}
    assert chart.transform == [alt.TimeUnitTransform(**kwds)]

    # window transform
    chart = alt.Chart().transform_window(xsum="sum(x)", ymin="min(y)", frame=[None, 0])
    window = [
        alt.WindowFieldDef(**{"as": "xsum", "field": "x", "op": "sum"}),
        alt.WindowFieldDef(**{"as": "ymin", "field": "y", "op": "min"}),
    ]

    # kwargs don't maintain order in Python < 3.6, so window list can
    # be reversed
    assert chart.transform in (
        [alt.WindowTransform(frame=[None, 0], window=window)],
        [alt.WindowTransform(frame=[None, 0], window=window[::-1])],
    )


def test_filter_transform_selection_predicates():
    selector1 = alt.selection_interval(name="s1")
    selector2 = alt.selection_interval(name="s2")
    base = alt.Chart("data.txt").mark_point()

    chart = base.transform_filter(selector1)
    assert chart.to_dict()["transform"] == [{"filter": {"param": "s1"}}]

    chart = base.transform_filter(~selector1)
    assert chart.to_dict()["transform"] == [{"filter": {"not": {"param": "s1"}}}]

    chart = base.transform_filter(selector1 & selector2)
    assert chart.to_dict()["transform"] == [
        {"filter": {"and": [{"param": "s1"}, {"param": "s2"}]}}
    ]

    chart = base.transform_filter(selector1 | selector2)
    assert chart.to_dict()["transform"] == [
        {"filter": {"or": [{"param": "s1"}, {"param": "s2"}]}}
    ]

    chart = base.transform_filter(selector1 | ~selector2)
    assert chart.to_dict()["transform"] == [
        {"filter": {"or": [{"param": "s1"}, {"not": {"param": "s2"}}]}}
    ]

    chart = base.transform_filter(~selector1 | ~selector2)
    assert chart.to_dict()["transform"] == [
        {"filter": {"or": [{"not": {"param": "s1"}}, {"not": {"param": "s2"}}]}}
    ]

    chart = base.transform_filter(~(selector1 & selector2))
    assert chart.to_dict()["transform"] == [
        {"filter": {"not": {"and": [{"param": "s1"}, {"param": "s2"}]}}}
    ]


def test_resolve_methods():
    chart = alt.LayerChart().resolve_axis(x="shared", y="independent")
    assert chart.resolve == alt.Resolve(
        axis=alt.AxisResolveMap(x="shared", y="independent")
    )

    chart = alt.LayerChart().resolve_legend(color="shared", fill="independent")
    assert chart.resolve == alt.Resolve(
        legend=alt.LegendResolveMap(color="shared", fill="independent")
    )

    chart = alt.LayerChart().resolve_scale(x="shared", y="independent")
    assert chart.resolve == alt.Resolve(
        scale=alt.ScaleResolveMap(x="shared", y="independent")
    )


def test_layer_encodings():
    chart = alt.LayerChart().encode(x="column:Q")
    assert chart.encoding.x == alt.X(shorthand="column:Q")


def test_add_selection():
    selections = [
        alt.selection_interval(),
        alt.selection_point(),
        alt.selection_point(),
    ]
    chart = (
        alt.Chart()
        .mark_point()
        .add_params(selections[0])
        .add_params(selections[1], selections[2])
    )
    expected = [s.param for s in selections]
    assert chart.params == expected


def test_repeat_add_selections():
    base = alt.Chart("data.csv").mark_point()
    selection = alt.selection_point()
    alt.Chart._counter = 0
    chart1 = base.add_params(selection).repeat(list("ABC"))
    alt.Chart._counter = 0
    chart2 = base.repeat(list("ABC")).add_params(selection)
    assert chart1.to_dict() == chart2.to_dict()


def test_facet_add_selections():
    base = alt.Chart("data.csv").mark_point()
    selection = alt.selection_point()
    alt.Chart._counter = 0
    chart1 = base.add_params(selection).facet("val:Q")
    alt.Chart._counter = 0
    chart2 = base.facet("val:Q").add_params(selection)
    assert chart1.to_dict() == chart2.to_dict()


def test_layer_add_selection():
    base = alt.Chart("data.csv").mark_point()
    selection = alt.selection_point()
    alt.Chart._counter = 0
    chart1 = alt.layer(base.add_params(selection), base)
    alt.Chart._counter = 0
    chart2 = alt.layer(base, base).add_params(selection)
    assert chart1.to_dict() == chart2.to_dict()


@pytest.mark.parametrize("charttype", [alt.concat, alt.hconcat, alt.vconcat])
def test_compound_add_selections(charttype):
    base = alt.Chart("data.csv").mark_point()
    selection = alt.selection_point()
    alt.Chart._counter = 0
    chart1 = charttype(base.add_params(selection), base.add_params(selection))
    alt.Chart._counter = 0
    chart2 = charttype(base, base).add_params(selection)
    assert chart1.to_dict() == chart2.to_dict()


def test_selection_property():
    sel = alt.selection_interval()
    chart = alt.Chart("data.csv").mark_point().properties(selection=sel)

    assert list(chart["selection"].keys()) == [sel.name]


def test_LookupData():
    df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    lookup = alt.LookupData(data=df, key="x")

    dct = lookup.to_dict()
    assert dct["key"] == "x"
    assert dct["data"] == {
        "values": [{"x": 1, "y": 4}, {"x": 2, "y": 5}, {"x": 3, "y": 6}]
    }


def test_themes():
    chart = alt.Chart("foo.txt").mark_point()

    with alt.themes.enable("default"):
        assert chart.to_dict()["config"] == {
            "view": {"continuousWidth": 300, "continuousHeight": 300}
        }

    with alt.themes.enable("opaque"):
        assert chart.to_dict()["config"] == {
            "background": "white",
            "view": {"continuousWidth": 300, "continuousHeight": 300},
        }

    with alt.themes.enable("none"):
        assert "config" not in chart.to_dict()


def test_chart_from_dict():
    base = alt.Chart("data.csv").mark_point().encode(x="x:Q", y="y:Q")

    charts = [
        base,
        base + base,
        base | base,
        base & base,
        base.facet("c:N"),
        (base + base).facet(row="c:N", data="data.csv"),
        base.repeat(["c", "d"]),
        (base + base).repeat(row=["c", "d"]),
    ]

    for chart in charts:
        chart_out = alt.Chart.from_dict(chart.to_dict())
        assert type(chart_out) is type(chart)

    # test that an invalid spec leads to a schema validation error
    with pytest.raises(jsonschema.ValidationError):
        alt.Chart.from_dict({"invalid": "spec"})


def test_consolidate_datasets(basic_chart):
    subchart1 = basic_chart
    subchart2 = basic_chart.copy()
    subchart2.data = basic_chart.data.copy()
    chart = subchart1 | subchart2

    with alt.data_transformers.enable(consolidate_datasets=True):
        dct_consolidated = chart.to_dict()

    with alt.data_transformers.enable(consolidate_datasets=False):
        dct_standard = chart.to_dict()

    assert "datasets" in dct_consolidated
    assert "datasets" not in dct_standard

    datasets = dct_consolidated["datasets"]

    # two dataset copies should be recognized as duplicates
    assert len(datasets) == 1

    # make sure data matches original & names are correct
    name, data = datasets.popitem()

    for spec in dct_standard["hconcat"]:
        assert spec["data"]["values"] == data

    for spec in dct_consolidated["hconcat"]:
        assert spec["data"] == {"name": name}


def test_consolidate_InlineData():
    data = alt.InlineData(
        values=[{"a": 1, "b": 1}, {"a": 2, "b": 2}], format={"type": "csv"}
    )
    chart = alt.Chart(data).mark_point()

    with alt.data_transformers.enable(consolidate_datasets=False):
        dct = chart.to_dict()
    assert dct["data"]["format"] == data.format
    assert dct["data"]["values"] == data.values

    with alt.data_transformers.enable(consolidate_datasets=True):
        dct = chart.to_dict()
    assert dct["data"]["format"] == data.format
    assert next(iter(dct["datasets"].values())) == data.values

    data = alt.InlineData(values=[], name="runtime_data")
    chart = alt.Chart(data).mark_point()

    with alt.data_transformers.enable(consolidate_datasets=False):
        dct = chart.to_dict()
    assert dct["data"] == data.to_dict()

    with alt.data_transformers.enable(consolidate_datasets=True):
        dct = chart.to_dict()
    assert dct["data"] == data.to_dict()


def test_repeat():
    # wrapped repeat
    chart1 = (
        alt.Chart("data.csv")
        .mark_point()
        .encode(
            x=alt.X(alt.repeat(), type="quantitative"),
            y="y:Q",
        )
        .repeat(["A", "B", "C", "D"], columns=2)
    )

    dct1 = chart1.to_dict()

    assert dct1["repeat"] == ["A", "B", "C", "D"]
    assert dct1["columns"] == 2
    assert dct1["spec"]["encoding"]["x"]["field"] == {"repeat": "repeat"}

    # explicit row/col repeat
    chart2 = (
        alt.Chart("data.csv")
        .mark_point()
        .encode(
            x=alt.X(alt.repeat("row"), type="quantitative"),
            y=alt.Y(alt.repeat("column"), type="quantitative"),
        )
        .repeat(row=["A", "B", "C"], column=["C", "B", "A"])
    )

    dct2 = chart2.to_dict()

    assert dct2["repeat"] == {"row": ["A", "B", "C"], "column": ["C", "B", "A"]}
    assert "columns" not in dct2
    assert dct2["spec"]["encoding"]["x"]["field"] == {"repeat": "row"}
    assert dct2["spec"]["encoding"]["y"]["field"] == {"repeat": "column"}


def test_data_property():
    data = pd.DataFrame({"x": [1, 2, 3], "y": list("ABC")})
    chart1 = alt.Chart(data).mark_point()
    chart2 = alt.Chart().mark_point().properties(data=data)

    assert chart1.to_dict() == chart2.to_dict()


@pytest.mark.parametrize("method", ["layer", "hconcat", "vconcat", "concat"])
@pytest.mark.parametrize(
    "data", ["data.json", pd.DataFrame({"x": range(3), "y": list("abc")})]
)
def test_subcharts_with_same_data(method, data):
    func = getattr(alt, method)

    point = alt.Chart(data).mark_point().encode(x="x:Q", y="y:Q")
    line = point.mark_line()
    text = point.mark_text()

    chart1 = func(point, line, text)
    assert chart1.data is not alt.Undefined
    assert all(c.data is alt.Undefined for c in getattr(chart1, method))

    if method != "concat":
        op = OP_DICT[method]
        chart2 = op(op(point, line), text)
        assert chart2.data is not alt.Undefined
        assert all(c.data is alt.Undefined for c in getattr(chart2, method))


@pytest.mark.parametrize("method", ["layer", "hconcat", "vconcat", "concat"])
@pytest.mark.parametrize(
    "data", ["data.json", pd.DataFrame({"x": range(3), "y": list("abc")})]
)
def test_subcharts_different_data(method, data):
    func = getattr(alt, method)

    point = alt.Chart(data).mark_point().encode(x="x:Q", y="y:Q")
    otherdata = alt.Chart("data.csv").mark_point().encode(x="x:Q", y="y:Q")
    nodata = alt.Chart().mark_point().encode(x="x:Q", y="y:Q")

    chart1 = func(point, otherdata)
    assert chart1.data is alt.Undefined
    assert getattr(chart1, method)[0].data is data

    chart2 = func(point, nodata)
    assert chart2.data is alt.Undefined
    assert getattr(chart2, method)[0].data is data


def test_layer_facet(basic_chart):
    chart = (basic_chart + basic_chart).facet(row="row:Q")
    assert chart.data is not alt.Undefined
    assert chart.spec.data is alt.Undefined
    for layer in chart.spec.layer:
        assert layer.data is alt.Undefined

    dct = chart.to_dict()
    assert "data" in dct


def test_layer_errors():
    toplevel_chart = alt.Chart("data.txt").mark_point().configure_legend(columns=2)

    facet_chart1 = alt.Chart("data.txt").mark_point().encode(facet="row:Q")

    facet_chart2 = alt.Chart("data.txt").mark_point().facet("row:Q")

    repeat_chart = alt.Chart("data.txt").mark_point().repeat(["A", "B", "C"])

    simple_chart = alt.Chart("data.txt").mark_point()

    with pytest.raises(ValueError) as err:  # noqa: PT011
        toplevel_chart + simple_chart
    assert str(err.value).startswith(
        'Objects with "config" attribute cannot be used within LayerChart.'
    )

    with pytest.raises(ValueError) as err:  # noqa: PT011
        alt.hconcat(simple_chart) + simple_chart
    assert (
        str(err.value)
        == "Concatenated charts cannot be layered. Instead, layer the charts before concatenating."
    )

    with pytest.raises(ValueError) as err:  # noqa: PT011
        repeat_chart + simple_chart
    assert (
        str(err.value)
        == "Repeat charts cannot be layered. Instead, layer the charts before repeating."
    )

    with pytest.raises(ValueError) as err:  # noqa: PT011
        facet_chart1 + simple_chart
    assert (
        str(err.value)
        == "Faceted charts cannot be layered. Instead, layer the charts before faceting."
    )

    with pytest.raises(ValueError) as err:  # noqa: PT011
        alt.layer(simple_chart) + facet_chart2
    assert (
        str(err.value)
        == "Faceted charts cannot be layered. Instead, layer the charts before faceting."
    )


@pytest.mark.parametrize(
    "chart_type",
    ["layer", "hconcat", "vconcat", "concat", "facet", "facet_encoding", "repeat"],
)
def test_resolve(chart_type):
    chart = _make_chart_type(chart_type)
    chart = (
        chart.resolve_scale(
            x="independent",
        )
        .resolve_legend(color="independent")
        .resolve_axis(y="independent")
    )
    dct = chart.to_dict()
    assert dct["resolve"] == {
        "scale": {"x": "independent"},
        "legend": {"color": "independent"},
        "axis": {"y": "independent"},
    }


# TODO: test vconcat, hconcat, concat, facet_encoding when schema allows them.
# This is blocked by https://github.com/vega/vega-lite/issues/5261
@pytest.mark.parametrize("chart_type", ["chart", "layer"])
@pytest.mark.parametrize("facet_arg", [None, "facet", "row", "column"])
def test_facet(chart_type, facet_arg):
    chart = _make_chart_type(chart_type)
    if facet_arg is None:
        chart = chart.facet("color:N", columns=2)
    else:
        chart = chart.facet(**{facet_arg: "color:N", "columns": 2})
    dct = chart.to_dict()

    assert "spec" in dct
    assert dct["columns"] == 2
    expected = {"field": "color", "type": "nominal"}
    if facet_arg is None or facet_arg == "facet":
        assert dct["facet"] == expected
    else:
        assert dct["facet"][facet_arg] == expected


def test_sequence():
    data = alt.sequence(100)
    assert data.to_dict() == {"sequence": {"start": 0, "stop": 100}}

    data = alt.sequence(5, 10)
    assert data.to_dict() == {"sequence": {"start": 5, "stop": 10}}

    data = alt.sequence(0, 1, 0.1, as_="x")
    assert data.to_dict() == {
        "sequence": {"start": 0, "stop": 1, "step": 0.1, "as": "x"}
    }


def test_graticule():
    data = alt.graticule()
    assert data.to_dict() == {"graticule": True}

    data = alt.graticule(step=[15, 15])
    assert data.to_dict() == {"graticule": {"step": [15, 15]}}


def test_sphere():
    data = alt.sphere()
    assert data.to_dict() == {"sphere": True}


def test_validate_dataset():
    d = {"data": {"values": [{}]}, "mark": {"type": "point"}}

    chart = alt.Chart.from_dict(d)
    jsn = chart.to_json()

    assert jsn
