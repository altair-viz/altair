# ruff: noqa: W291
import copy
import io
import inspect
import json
import jsonschema
import jsonschema.exceptions
import pickle
import warnings

import numpy as np
import pandas as pd
import pytest
from vega_datasets import data

import altair as alt
from altair import load_schema
from altair.utils.schemapi import (
    UndefinedType,
    SchemaBase,
    Undefined,
    _FromDict,
    SchemaValidationError,
    _DEFAULT_JSON_SCHEMA_DRAFT_URL,
)

_JSON_SCHEMA_DRAFT_URL = load_schema()["$schema"]
# Make tests inherit from _TestSchema, so that when we test from_dict it won't
# try to use SchemaBase objects defined elsewhere as wrappers.


def test_actual_json_schema_draft_is_same_as_hardcoded_default():
    # See comments next to definition of _DEFAULT_JSON_SCHEMA_DRAFT_URL
    # for details why we need this test
    assert _DEFAULT_JSON_SCHEMA_DRAFT_URL == _JSON_SCHEMA_DRAFT_URL, (
        "The default json schema URL, which is hardcoded,"
        + " is not the same as the one used in the Vega-Lite schema."
        + " You need to update the default value."
    )


class _TestSchema(SchemaBase):
    @classmethod
    def _default_wrapper_classes(cls):
        return _TestSchema.__subclasses__()


class MySchema(_TestSchema):
    _schema = {
        "$schema": _JSON_SCHEMA_DRAFT_URL,
        "definitions": {
            "StringMapping": {
                "type": "object",
                "additionalProperties": {"type": "string"},
            },
            "StringArray": {"type": "array", "items": {"type": "string"}},
        },
        "properties": {
            "a": {"$ref": "#/definitions/StringMapping"},
            "a2": {"type": "object", "additionalProperties": {"type": "number"}},
            "b": {"$ref": "#/definitions/StringArray"},
            "b2": {"type": "array", "items": {"type": "number"}},
            "c": {"type": ["string", "number"]},
            "d": {
                "anyOf": [
                    {"$ref": "#/definitions/StringMapping"},
                    {"$ref": "#/definitions/StringArray"},
                ]
            },
            "e": {"items": [{"type": "string"}, {"type": "string"}]},
        },
    }


class StringMapping(_TestSchema):
    _schema = {"$ref": "#/definitions/StringMapping"}
    _rootschema = MySchema._schema


class StringArray(_TestSchema):
    _schema = {"$ref": "#/definitions/StringArray"}
    _rootschema = MySchema._schema


class Derived(_TestSchema):
    _schema = {
        "$schema": _JSON_SCHEMA_DRAFT_URL,
        "definitions": {
            "Foo": {"type": "object", "properties": {"d": {"type": "string"}}},
            "Bar": {"type": "string", "enum": ["A", "B"]},
        },
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "string"},
            "c": {"$ref": "#/definitions/Foo"},
        },
    }


class Foo(_TestSchema):
    _schema = {"$ref": "#/definitions/Foo"}
    _rootschema = Derived._schema


class Bar(_TestSchema):
    _schema = {"$ref": "#/definitions/Bar"}
    _rootschema = Derived._schema


class SimpleUnion(_TestSchema):
    _schema = {
        "$schema": _JSON_SCHEMA_DRAFT_URL,
        "anyOf": [{"type": "integer"}, {"type": "string"}],
    }


class DefinitionUnion(_TestSchema):
    _schema = {"anyOf": [{"$ref": "#/definitions/Foo"}, {"$ref": "#/definitions/Bar"}]}
    _rootschema = Derived._schema


class SimpleArray(_TestSchema):
    _schema = {
        "$schema": _JSON_SCHEMA_DRAFT_URL,
        "type": "array",
        "items": {"anyOf": [{"type": "integer"}, {"type": "string"}]},
    }


class InvalidProperties(_TestSchema):
    _schema = {
        "$schema": _JSON_SCHEMA_DRAFT_URL,
        "type": "object",
        "properties": {"for": {}, "as": {}, "vega-lite": {}, "$schema": {}},
    }


_validation_selection_schema = {
    "properties": {
        "e": {"type": "number", "exclusiveMinimum": 10},
    },
}


class Draft4Schema(_TestSchema):
    _schema = {
        **_validation_selection_schema,
        "$schema": "http://json-schema.org/draft-04/schema#",
    }


class Draft6Schema(_TestSchema):
    _schema = {
        **_validation_selection_schema,
        "$schema": "http://json-schema.org/draft-06/schema#",
    }


def test_construct_multifaceted_schema():
    dct = {
        "a": {"foo": "bar"},
        "a2": {"foo": 42},
        "b": ["a", "b", "c"],
        "b2": [1, 2, 3],
        "c": 42,
        "d": ["x", "y", "z"],
        "e": ["a", "b"],
    }

    myschema = MySchema.from_dict(dct)
    assert myschema.to_dict() == dct

    myschema2 = MySchema(**dct)
    assert myschema2.to_dict() == dct

    assert isinstance(myschema.a, StringMapping)
    assert isinstance(myschema.a2, dict)
    assert isinstance(myschema.b, StringArray)
    assert isinstance(myschema.b2, list)
    assert isinstance(myschema.d, StringArray)


def test_schema_cases():
    assert Derived(a=4, b="yo").to_dict() == {"a": 4, "b": "yo"}
    assert Derived(a=4, c={"d": "hey"}).to_dict() == {"a": 4, "c": {"d": "hey"}}
    assert Derived(a=4, b="5", c=Foo(d="val")).to_dict() == {
        "a": 4,
        "b": "5",
        "c": {"d": "val"},
    }
    assert Foo(d="hello", f=4).to_dict() == {"d": "hello", "f": 4}

    assert Derived().to_dict() == {}
    assert Foo().to_dict() == {}

    with pytest.raises(jsonschema.ValidationError):
        # a needs to be an integer
        Derived(a="yo").to_dict()

    with pytest.raises(jsonschema.ValidationError):
        # Foo.d needs to be a string
        Derived(c=Foo(4)).to_dict()

    with pytest.raises(jsonschema.ValidationError):
        # no additional properties allowed
        Derived(foo="bar").to_dict()


def test_round_trip():
    D = {"a": 4, "b": "yo"}
    assert Derived.from_dict(D).to_dict() == D

    D = {"a": 4, "c": {"d": "hey"}}
    assert Derived.from_dict(D).to_dict() == D

    D = {"a": 4, "b": "5", "c": {"d": "val"}}
    assert Derived.from_dict(D).to_dict() == D

    D = {"d": "hello", "f": 4}
    assert Foo.from_dict(D).to_dict() == D


def test_from_dict():
    D = {"a": 4, "b": "5", "c": {"d": "val"}}
    obj = Derived.from_dict(D)
    assert obj.a == 4
    assert obj.b == "5"
    assert isinstance(obj.c, Foo)


def test_simple_type():
    assert SimpleUnion(4).to_dict() == 4


def test_simple_array():
    assert SimpleArray([4, 5, "six"]).to_dict() == [4, 5, "six"]
    assert SimpleArray.from_dict(list("abc")).to_dict() == list("abc")


def test_definition_union():
    obj = DefinitionUnion.from_dict("A")
    assert isinstance(obj, Bar)
    assert obj.to_dict() == "A"

    obj = DefinitionUnion.from_dict("B")
    assert isinstance(obj, Bar)
    assert obj.to_dict() == "B"

    obj = DefinitionUnion.from_dict({"d": "yo"})
    assert isinstance(obj, Foo)
    assert obj.to_dict() == {"d": "yo"}


def test_invalid_properties():
    dct = {"for": 2, "as": 3, "vega-lite": 4, "$schema": 5}
    invalid = InvalidProperties.from_dict(dct)
    assert invalid["for"] == 2
    assert invalid["as"] == 3
    assert invalid["vega-lite"] == 4
    assert invalid["$schema"] == 5
    assert invalid.to_dict() == dct


def test_undefined_singleton():
    assert Undefined is UndefinedType()


def test_schema_validator_selection():
    # Tests if the correct validator class is chosen based on the $schema
    # property in the schema. This uses a backwards-incompatible change
    # in Draft 6 which introduced exclusiveMinimum as a number instead of a boolean.
    # Therefore, with Draft 4 there is no actual minimum set as a number and validating
    # the dictionary below passes. With Draft 6, it correctly checks if the number is
    # > 10 and raises a ValidationError. See
    # https://json-schema.org/draft-06/json-schema-release-notes.html#q-what-are-
    # the-changes-between-draft-04-and-draft-06 for more details
    dct = {
        "e": 9,
    }

    assert Draft4Schema.from_dict(dct).to_dict() == dct
    with pytest.raises(
        jsonschema.exceptions.ValidationError,
        match="9 is less than or equal to the minimum of 10",
    ):
        Draft6Schema.from_dict(dct)


@pytest.fixture()
def dct():
    return {
        "a": {"foo": "bar"},
        "a2": {"foo": 42},
        "b": ["a", "b", "c"],
        "b2": [1, 2, 3],
        "c": 42,
        "d": ["x", "y", "z"],
    }


def test_copy_method(dct):
    myschema = MySchema.from_dict(dct)

    # Make sure copy is deep
    copy = myschema.copy(deep=True)
    copy["a"]["foo"] = "new value"
    copy["b"] = ["A", "B", "C"]
    copy["c"] = 164
    assert myschema.to_dict() == dct

    # If we ignore a value, changing the copy changes the original
    copy = myschema.copy(deep=True, ignore=["a"])
    copy["a"]["foo"] = "new value"
    copy["b"] = ["A", "B", "C"]
    copy["c"] = 164
    mydct = myschema.to_dict()
    assert mydct["a"]["foo"] == "new value"
    assert mydct["b"][0] == dct["b"][0]
    assert mydct["c"] == dct["c"]

    # If copy is not deep, then changing copy below top level changes original
    copy = myschema.copy(deep=False)
    copy["a"]["foo"] = "baz"
    copy["b"] = ["A", "B", "C"]
    copy["c"] = 164
    mydct = myschema.to_dict()
    assert mydct["a"]["foo"] == "baz"
    assert mydct["b"] == dct["b"]
    assert mydct["c"] == dct["c"]


def test_copy_module(dct):
    myschema = MySchema.from_dict(dct)

    cp = copy.deepcopy(myschema)
    cp["a"]["foo"] = "new value"
    cp["b"] = ["A", "B", "C"]
    cp["c"] = 164
    assert myschema.to_dict() == dct


def test_attribute_error():
    m = MySchema()
    invalid_attr = "invalid_attribute"
    with pytest.raises(AttributeError) as err:
        getattr(m, invalid_attr)
    assert str(err.value) == (
        "'MySchema' object has no attribute " "'invalid_attribute'"
    )


def test_to_from_json(dct):
    json_str = MySchema.from_dict(dct).to_json()
    new_dct = MySchema.from_json(json_str).to_dict()

    assert new_dct == dct


def test_to_from_pickle(dct):
    myschema = MySchema.from_dict(dct)
    output = io.BytesIO()
    pickle.dump(myschema, output)
    output.seek(0)
    myschema_new = pickle.load(output)

    assert myschema_new.to_dict() == dct


def test_class_with_no_schema():
    class BadSchema(SchemaBase):
        pass

    with pytest.raises(ValueError) as err:  # noqa: PT011
        BadSchema(4)
    assert str(err.value).startswith("Cannot instantiate object")


@pytest.mark.parametrize("use_json", [True, False])
def test_hash_schema(use_json):
    classes = _TestSchema._default_wrapper_classes()

    for cls in classes:
        hsh1 = _FromDict.hash_schema(cls._schema, use_json=use_json)
        hsh2 = _FromDict.hash_schema(cls._schema, use_json=use_json)
        assert hsh1 == hsh2
        assert hash(hsh1) == hash(hsh2)


def test_schema_validation_error():
    try:
        MySchema(a={"foo": 4})
        the_err = None
    except jsonschema.ValidationError as err:
        the_err = err

    assert isinstance(the_err, SchemaValidationError)
    message = str(the_err)

    assert the_err.message in message


def chart_error_example__layer():
    # Error: Width is not a valid property of a VConcatChart
    points = (
        alt.Chart(data.cars.url)
        .mark_point()
        .encode(
            x="Horsepower:Q",
            y="Miles_per_Gallon:Q",
        )
    )
    return (points & points).properties(width=400)


def chart_error_example__hconcat():
    # Error: Invalid value for title in Text
    source = data.cars()
    points = (
        alt.Chart(source)
        .mark_point()
        .encode(
            x="Horsepower",
            y="Miles_per_Gallon",
        )
    )

    text = (
        alt.Chart(source)
        .mark_text()
        .encode(
            alt.Text("Horsepower:N", title={"text": "Horsepower", "align": "right"})
        )
    )

    return points | text


def chart_error_example__invalid_y_option_value_unknown_x_option():
    # Error 1: unknown is an invalid channel option for X
    # Error 2: Invalid Y option value "asdf" and unknown option "unknown" for X
    return (
        alt.Chart(data.barley())
        .mark_bar()
        .encode(
            x=alt.X("variety", unknown=2),
            y=alt.Y("sum(yield)", stack="asdf"),
        )
    )


def chart_error_example__invalid_y_option_value():
    # Error: Invalid Y option value "asdf"
    return (
        alt.Chart(data.barley())
        .mark_bar()
        .encode(
            x=alt.X("variety"),
            y=alt.Y("sum(yield)", stack="asdf"),
        )
    )


def chart_error_example__invalid_y_option_value_with_condition():
    # Error: Invalid Y option value "asdf". Condition is correct
    # but is added below as in previous implementations of Altair this interfered
    # with finding the invalidChannel error
    return (
        alt.Chart(data.barley())
        .mark_bar()
        .encode(
            x="variety",
            y=alt.Y("sum(yield)", stack="asdf"),
            opacity=alt.condition("datum.yield > 0", alt.value(1), alt.value(0.2)),
        )
    )


def chart_error_example__invalid_timeunit_value():
    # Error: Invalid value for Angle.timeUnit
    return alt.Chart().encode(alt.Angle().timeUnit("invalid_value"))


def chart_error_example__invalid_sort_value():
    # Error: Invalid value for Angle.sort
    return alt.Chart().encode(alt.Angle().sort("invalid_value"))


def chart_error_example__invalid_bandposition_value():
    # Error: Invalid value for Text.bandPosition
    return (
        alt.Chart(data.cars())
        .mark_text(align="right")
        .encode(alt.Text("Horsepower:N", bandPosition="4"))
    )


def chart_error_example__invalid_type():
    # Error: Invalid value for type
    return alt.Chart().encode(alt.X(type="unknown"))


def chart_error_example__additional_datum_argument():
    # Error: wrong_argument is not a valid argument to datum
    return alt.Chart().mark_point().encode(x=alt.datum(1, wrong_argument=1))


def chart_error_example__invalid_value_type():
    # Error: Value cannot be an integer in this case
    return (
        alt.Chart(data.cars())
        .mark_point()
        .encode(
            x="Acceleration:Q",
            y="Horsepower:Q",
            color=alt.value(1),  # should be eg. alt.value('red')
        )
    )


def chart_error_example__wrong_tooltip_type_in_faceted_chart():
    # Error: Wrong data type to pass to tooltip
    return (
        alt.Chart(pd.DataFrame({"a": [1]}))
        .mark_point()
        .encode(tooltip=[{"wrong"}])
        .facet()
    )


def chart_error_example__wrong_tooltip_type_in_layered_chart():
    # Error: Wrong data type to pass to tooltip
    return alt.layer(
        alt.Chart().mark_point().encode(tooltip=[{"wrong"}]),
    )


def chart_error_example__two_errors_in_layered_chart():
    # Error 1: Wrong data type to pass to tooltip
    # Error 2: `Color` has no parameter named 'invalidArgument'
    return alt.layer(
        alt.Chart().mark_point().encode(tooltip=[{"wrong"}]),
        alt.Chart().mark_line().encode(alt.Color(invalidArgument="unknown")),
    )


def chart_error_example__two_errors_in_complex_concat_layered_chart():
    # Error 1: Wrong data type to pass to tooltip
    # Error 2: Invalid value for bandPosition
    return (
        chart_error_example__wrong_tooltip_type_in_layered_chart()
        | chart_error_example__invalid_bandposition_value()
    )


def chart_error_example__three_errors_in_complex_concat_layered_chart():
    # Error 1: Wrong data type to pass to tooltip
    # Error 2: `Color` has no parameter named 'invalidArgument'
    # Error 3: Invalid value for bandPosition
    return (
        chart_error_example__two_errors_in_layered_chart()
        | chart_error_example__invalid_bandposition_value()
    )


def chart_error_example__two_errors_with_one_in_nested_layered_chart():
    # Error 1: invalidOption is not a valid option for Scale
    # Error 2: `Color` has no parameter named 'invalidArgument'

    # In the final chart object, the `layer` attribute will look like this:
    # [alt.Chart(...), alt.Chart(...), alt.LayerChart(...)]
    # We can therefore use this example to test if an error is also
    # spotted in a layered chart within another layered chart
    source = pd.DataFrame(
        [
            {"Day": 1, "Value": 103.3},
            {"Day": 2, "Value": 394.8},
            {"Day": 3, "Value": 199.5},
        ]
    )

    blue_bars = (
        alt.Chart(source)
        .encode(alt.X("Day:O").scale(invalidOption=10), alt.Y("Value:Q"))
        .mark_bar()
    )
    red_bars = (
        alt.Chart(source)
        .transform_filter(alt.datum.Value >= 300)
        .transform_calculate(as_="baseline", calculate="300")
        .encode(
            alt.X("Day:O"),
            alt.Y("baseline:Q"),
            alt.Y2("Value:Q"),
            color=alt.value("#e45755"),
        )
        .mark_bar()
    )

    bars = blue_bars + red_bars

    base = alt.Chart().encode(y=alt.datum(300))

    rule = base.mark_rule().encode(alt.Color(invalidArgument="unknown"))
    text = base.mark_text(text="hazardous")
    rule_text = rule + text

    chart = bars + rule_text
    return chart


def chart_error_example__four_errors():
    # Error 1: unknown is not a valid encoding channel option
    # Error 2: Invalid Y option value "asdf".
    # Error 3: another_unknown is not a valid encoding channel option
    # Error 4: fourth_error is not a valid encoding channel option <- this error
    # should not show up in the final error message as it is capped at showing
    # 3 errors
    return (
        alt.Chart(data.barley())
        .mark_bar()
        .encode(
            x=alt.X("variety", unknown=2),
            y=alt.Y("sum(yield)", stack="asdf"),
            color=alt.Color("variety", another_unknown=2),
            opacity=alt.Opacity("variety", fourth_error=1),
        )
    )


@pytest.mark.parametrize(
    ("chart_func", "expected_error_message"),
    [
        (
            chart_error_example__invalid_y_option_value_unknown_x_option,
            inspect.cleandoc(
                r"""Multiple errors were found.

                Error 1: `X` has no parameter named 'unknown'

                    Existing parameter names are:
                    shorthand      bin      scale   timeUnit   
                    aggregate      field    sort    title      
                    axis           impute   stack   type       
                    bandPosition                               

                    See the help for `X` to read the full description of these parameters

                Error 2: 'asdf' is an invalid value for `stack`. Valid values are:

                    - One of \['zero', 'center', 'normalize'\]
                    - Of type 'null' or 'boolean'$"""
            ),
        ),
        (
            chart_error_example__wrong_tooltip_type_in_faceted_chart,
            inspect.cleandoc(
                r"""'{'wrong'}' is an invalid value for `field`. Valid values are of type 'string' or 'object'.$"""
            ),
        ),
        (
            chart_error_example__wrong_tooltip_type_in_layered_chart,
            inspect.cleandoc(
                r"""'{'wrong'}' is an invalid value for `field`. Valid values are of type 'string' or 'object'.$"""
            ),
        ),
        (
            chart_error_example__two_errors_in_layered_chart,
            inspect.cleandoc(
                r"""Multiple errors were found.

                Error 1: '{'wrong'}' is an invalid value for `field`. Valid values are of type 'string' or 'object'.

                Error 2: `Color` has no parameter named 'invalidArgument'

                    Existing parameter names are:
                    shorthand      bin         legend   timeUnit   
                    aggregate      condition   scale    title      
                    bandPosition   field       sort     type       

                    See the help for `Color` to read the full description of these parameters$"""
            ),
        ),
        (
            chart_error_example__two_errors_in_complex_concat_layered_chart,
            inspect.cleandoc(
                r"""Multiple errors were found.

                Error 1: '{'wrong'}' is an invalid value for `field`. Valid values are of type 'string' or 'object'.

                Error 2: '4' is an invalid value for `bandPosition`. Valid values are of type 'number'.$"""
            ),
        ),
        (
            chart_error_example__three_errors_in_complex_concat_layered_chart,
            inspect.cleandoc(
                r"""Multiple errors were found.

                Error 1: '{'wrong'}' is an invalid value for `field`. Valid values are of type 'string' or 'object'.

                Error 2: `Color` has no parameter named 'invalidArgument'

                    Existing parameter names are:
                    shorthand      bin         legend   timeUnit   
                    aggregate      condition   scale    title      
                    bandPosition   field       sort     type       

                    See the help for `Color` to read the full description of these parameters

                Error 3: '4' is an invalid value for `bandPosition`. Valid values are of type 'number'.$"""
            ),
        ),
        (
            chart_error_example__two_errors_with_one_in_nested_layered_chart,
            inspect.cleandoc(
                r"""Multiple errors were found.

                Error 1: `Scale` has no parameter named 'invalidOption'

                    Existing parameter names are:
                    align      domain      exponent       paddingOuter   round    
                    base       domainMax   interpolate    range          scheme   
                    bins       domainMid   nice           rangeMax       type     
                    clamp      domainMin   padding        rangeMin       zero     
                    constant   domainRaw   paddingInner   reverse                 

                    See the help for `Scale` to read the full description of these parameters

                Error 2: `Color` has no parameter named 'invalidArgument'

                    Existing parameter names are:
                    shorthand      bin         legend   timeUnit   
                    aggregate      condition   scale    title      
                    bandPosition   field       sort     type       

                    See the help for `Color` to read the full description of these parameters$"""
            ),
        ),
        (
            chart_error_example__layer,
            inspect.cleandoc(
                r"""`VConcatChart` has no parameter named 'width'

                Existing parameter names are:
                vconcat      center     description   params    title       
                autosize     config     name          resolve   transform   
                background   data       padding       spacing   usermeta    
                bounds       datasets                                       

                See the help for `VConcatChart` to read the full description of these parameters$"""
            ),
        ),
        (
            chart_error_example__invalid_y_option_value,
            inspect.cleandoc(
                r"""'asdf' is an invalid value for `stack`. Valid values are:

                - One of \['zero', 'center', 'normalize'\]
                - Of type 'null' or 'boolean'$"""
            ),
        ),
        (
            chart_error_example__invalid_y_option_value_with_condition,
            inspect.cleandoc(
                r"""'asdf' is an invalid value for `stack`. Valid values are:

                - One of \['zero', 'center', 'normalize'\]
                - Of type 'null' or 'boolean'$"""
            ),
        ),
        (
            chart_error_example__hconcat,
            inspect.cleandoc(
                r"""'{'text': 'Horsepower', 'align': 'right'}' is an invalid value for `title`. Valid values are of type 'string', 'array', or 'null'.$"""
            ),
        ),
        (
            chart_error_example__invalid_timeunit_value,
            inspect.cleandoc(
                r"""'invalid_value' is an invalid value for `timeUnit`. Valid values are:

                - One of \['year', 'quarter', 'month', 'week', 'day', 'dayofyear', 'date', 'hours', 'minutes', 'seconds', 'milliseconds'\]
                - One of \['utcyear', 'utcquarter', 'utcmonth', 'utcweek', 'utcday', 'utcdayofyear', 'utcdate', 'utchours', 'utcminutes', 'utcseconds', 'utcmilliseconds'\]
                - One of \['yearquarter', 'yearquartermonth', 'yearmonth', 'yearmonthdate', 'yearmonthdatehours', 'yearmonthdatehoursminutes', 'yearmonthdatehoursminutesseconds', 'yearweek', 'yearweekday', 'yearweekdayhours', 'yearweekdayhoursminutes', 'yearweekdayhoursminutesseconds', 'yeardayofyear', 'quartermonth', 'monthdate', 'monthdatehours', 'monthdatehoursminutes', 'monthdatehoursminutesseconds', 'weekday', 'weekdayhours', 'weekdayhoursminutes', 'weekdayhoursminutesseconds', 'dayhours', 'dayhoursminutes', 'dayhoursminutesseconds', 'hoursminutes', 'hoursminutesseconds', 'minutesseconds', 'secondsmilliseconds'\]
                - One of \['utcyearquarter', 'utcyearquartermonth', 'utcyearmonth', 'utcyearmonthdate', 'utcyearmonthdatehours', 'utcyearmonthdatehoursminutes', 'utcyearmonthdatehoursminutesseconds', 'utcyearweek', 'utcyearweekday', 'utcyearweekdayhours', 'utcyearweekdayhoursminutes', 'utcyearweekdayhoursminutesseconds', 'utcyeardayofyear', 'utcquartermonth', 'utcmonthdate', 'utcmonthdatehours', 'utcmonthdatehoursminutes', 'utcmonthdatehoursminutesseconds', 'utcweekday', 'utcweeksdayhours', 'utcweekdayhoursminutes', 'utcweekdayhoursminutesseconds', 'utcdayhours', 'utcdayhoursminutes', 'utcdayhoursminutesseconds', 'utchoursminutes', 'utchoursminutesseconds', 'utcminutesseconds', 'utcsecondsmilliseconds'\]
                - One of \['binnedyear', 'binnedyearquarter', 'binnedyearquartermonth', 'binnedyearmonth', 'binnedyearmonthdate', 'binnedyearmonthdatehours', 'binnedyearmonthdatehoursminutes', 'binnedyearmonthdatehoursminutesseconds', 'binnedyearweek', 'binnedyearweekday', 'binnedyearweekdayhours', 'binnedyearweekdayhoursminutes', 'binnedyearweekdayhoursminutesseconds', 'binnedyeardayofyear'\]
                - One of \['binnedutcyear', 'binnedutcyearquarter', 'binnedutcyearquartermonth', 'binnedutcyearmonth', 'binnedutcyearmonthdate', 'binnedutcyearmonthdatehours', 'binnedutcyearmonthdatehoursminutes', 'binnedutcyearmonthdatehoursminutesseconds', 'binnedutcyearweek', 'binnedutcyearweekday', 'binnedutcyearweekdayhours', 'binnedutcyearweekdayhoursminutes', 'binnedutcyearweekdayhoursminutesseconds', 'binnedutcyeardayofyear'\]
                - Of type 'object'$"""
            ),
        ),
        (
            chart_error_example__invalid_sort_value,
            inspect.cleandoc(
                r"""'invalid_value' is an invalid value for `sort`. Valid values are:

                - One of \['ascending', 'descending'\]
                - One of \['x', 'y', 'color', 'fill', 'stroke', 'strokeWidth', 'size', 'shape', 'fillOpacity', 'strokeOpacity', 'opacity', 'text'\]
                - One of \['-x', '-y', '-color', '-fill', '-stroke', '-strokeWidth', '-size', '-shape', '-fillOpacity', '-strokeOpacity', '-opacity', '-text'\]
                - Of type 'array', 'object', or 'null'$"""
            ),
        ),
        (
            chart_error_example__invalid_bandposition_value,
            inspect.cleandoc(
                r"""'4' is an invalid value for `bandPosition`. Valid values are of type 'number'.$"""
            ),
        ),
        (
            chart_error_example__invalid_type,
            inspect.cleandoc(
                r"""'unknown' is an invalid value for `type`. Valid values are one of \['quantitative', 'ordinal', 'temporal', 'nominal', 'geojson'\].$"""
            ),
        ),
        (
            chart_error_example__additional_datum_argument,
            inspect.cleandoc(
                r"""`X` has no parameter named 'wrong_argument'

                Existing parameter names are:
                shorthand      bin      scale   timeUnit   
                aggregate      field    sort    title      
                axis           impute   stack   type       
                bandPosition                               

                See the help for `X` to read the full description of these parameters$"""
            ),
        ),
        (
            chart_error_example__invalid_value_type,
            inspect.cleandoc(
                r"""'1' is an invalid value for `value`. Valid values are of type 'object', 'string', or 'null'.$"""
            ),
        ),
        (
            chart_error_example__four_errors,
            inspect.cleandoc(
                r"""Multiple errors were found.

                Error 1: `Color` has no parameter named 'another_unknown'

                    Existing parameter names are:
                    shorthand      bin         legend   timeUnit   
                    aggregate      condition   scale    title      
                    bandPosition   field       sort     type       

                    See the help for `Color` to read the full description of these parameters

                Error 2: `Opacity` has no parameter named 'fourth_error'

                    Existing parameter names are:
                    shorthand      bin         legend   timeUnit   
                    aggregate      condition   scale    title      
                    bandPosition   field       sort     type       

                    See the help for `Opacity` to read the full description of these parameters

                Error 3: `X` has no parameter named 'unknown'

                    Existing parameter names are:
                    shorthand      bin      scale   timeUnit   
                    aggregate      field    sort    title      
                    axis           impute   stack   type       
                    bandPosition                               

                    See the help for `X` to read the full description of these parameters$"""
            ),
        ),
    ],
)
def test_chart_validation_errors(chart_func, expected_error_message):
    # For some wrong chart specifications such as an unknown encoding channel,
    # Altair already raises a warning before the chart specifications are validated.
    # We can ignore these warnings as we are interested in the errors being raised
    # during validation which is triggered by to_dict
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        chart = chart_func()
    with pytest.raises(SchemaValidationError, match=expected_error_message):
        chart.to_dict()


def test_multiple_field_strings_in_condition():
    selection = alt.selection_point()
    expected_error_message = "A field cannot be used for both the `if_true` and `if_false` values of a condition. One of them has to specify a `value` or `datum` definition."
    with pytest.raises(ValueError, match=expected_error_message):
        (
            alt.Chart(data.cars())
            .mark_circle()
            .add_params(selection)
            .encode(
                color=alt.condition(selection, "Origin", "Origin"),
            )
        ).to_dict()


def test_serialize_numpy_types():
    m = MySchema(
        a={"date": np.datetime64("2019-01-01")},
        a2={"int64": np.int64(1), "float64": np.float64(2)},
        b2=np.arange(4),
    )
    out = m.to_json()
    dct = json.loads(out)
    assert dct == {
        "a": {"date": "2019-01-01"},
        "a2": {"int64": 1, "float64": 2},
        "b2": [0, 1, 2, 3],
    }


def test_to_dict_no_side_effects():
    # Tests that shorthands are expanded in returned dictionary when calling to_dict
    # but that they remain untouched in the chart object. Goal is to ensure that
    # the chart object stays unchanged when to_dict is called
    def validate_encoding(encoding):
        assert encoding.x["shorthand"] == "a"
        assert encoding.x["field"] is alt.Undefined
        assert encoding.x["type"] is alt.Undefined
        assert encoding.y["shorthand"] == "b:Q"
        assert encoding.y["field"] is alt.Undefined
        assert encoding.y["type"] is alt.Undefined

    data = pd.DataFrame(
        {
            "a": ["A", "B", "C", "D", "E", "F", "G", "H", "I"],
            "b": [28, 55, 43, 91, 81, 53, 19, 87, 52],
        }
    )

    chart = alt.Chart(data).mark_bar().encode(x="a", y="b:Q")

    validate_encoding(chart.encoding)
    dct = chart.to_dict()
    validate_encoding(chart.encoding)

    assert "shorthand" not in dct["encoding"]["x"]
    assert dct["encoding"]["x"]["field"] == "a"

    assert "shorthand" not in dct["encoding"]["y"]
    assert dct["encoding"]["y"]["field"] == "b"
    assert dct["encoding"]["y"]["type"] == "quantitative"


def test_to_dict_expand_mark_spec():
    # Test that `to_dict` correctly expands marks to a dictionary
    # without impacting the original spec which remains a string
    chart = alt.Chart().mark_bar()
    assert chart.to_dict()["mark"] == {"type": "bar"}
    assert chart.mark == "bar"
