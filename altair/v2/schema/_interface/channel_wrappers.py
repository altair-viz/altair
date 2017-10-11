# -*- coding: utf-8 -*-
# Auto-generated file: do not modify directly
# - altair version info: v1.2.0-113-g9a32e45
# - date: 2017-08-17 14:33:49

import pandas as pd

from . import jstraitlets as jst
from . import schema
from ...traitlet_utils import parse_shorthand, infer_vegalite_type


class ConditionalNumberLegend(schema.ConditionalNumberLegendDef):
    """Wrapper for Vega-Lite ConditionalNumberLegendDef definition.
    Generic type for conditional channelDef.
    F defines the underlying FieldDef type while V defines the
    underlying ValueDef type.
    Attributes
    ----------
    shorthand: Unicode
        A shorthand description of the channel
    """
    # Traitlets
    shorthand = jst.JSONString(default_value='', help="Shorthand specification of field, optionally including the aggregate and type (see :ref:`shorthand-description`)")
    _skip_on_export = ['shorthand']

    # Class Methods
    def __init__(self, shorthand='', **kwargs):
        kwargs['shorthand'] = shorthand
        kwds = dict()
        kwargs.update({k:v for k, v in kwds.items() if v is not jst.undefined})
        super(ConditionalNumberLegend, self).__init__(**kwargs)

    def _finalize(self, **kwargs):
        """Finalize object: this involves inferring types if necessary"""
        # parse the shorthand to extract the field, type, and aggregate
        for key, val in parse_shorthand(self.shorthand).items():
            setattr(self, key, val)

        # infer the type if not already specified
        if self.type is jst.undefined:
            data = kwargs.get('data', jst.undefined)
            if isinstance(data, pd.DataFrame) and self.field in data:
                self.type = infer_vegalite_type(data[self.field])

        super(ConditionalNumberLegend, self)._finalize(**kwargs)


class ConditionalStringLegend(schema.ConditionalStringLegendDef):
    """Wrapper for Vega-Lite ConditionalStringLegendDef definition.
    Generic type for conditional channelDef.
    F defines the underlying FieldDef type while V defines the
    underlying ValueDef type.
    Attributes
    ----------
    shorthand: Unicode
        A shorthand description of the channel
    """
    # Traitlets
    shorthand = jst.JSONString(default_value='', help="Shorthand specification of field, optionally including the aggregate and type (see :ref:`shorthand-description`)")
    _skip_on_export = ['shorthand']

    # Class Methods
    def __init__(self, shorthand='', **kwargs):
        kwargs['shorthand'] = shorthand
        kwds = dict()
        kwargs.update({k:v for k, v in kwds.items() if v is not jst.undefined})
        super(ConditionalStringLegend, self).__init__(**kwargs)

    def _finalize(self, **kwargs):
        """Finalize object: this involves inferring types if necessary"""
        # parse the shorthand to extract the field, type, and aggregate
        for key, val in parse_shorthand(self.shorthand).items():
            setattr(self, key, val)

        # infer the type if not already specified
        if self.type is jst.undefined:
            data = kwargs.get('data', jst.undefined)
            if isinstance(data, pd.DataFrame) and self.field in data:
                self.type = infer_vegalite_type(data[self.field])

        super(ConditionalStringLegend, self)._finalize(**kwargs)


class ConditionalText(schema.ConditionalTextDef):
    """Wrapper for Vega-Lite ConditionalTextDef definition.
    Generic type for conditional channelDef.
    F defines the underlying FieldDef type while V defines the
    underlying ValueDef type.
    Attributes
    ----------
    shorthand: Unicode
        A shorthand description of the channel
    """
    # Traitlets
    shorthand = jst.JSONString(default_value='', help="Shorthand specification of field, optionally including the aggregate and type (see :ref:`shorthand-description`)")
    _skip_on_export = ['shorthand']

    # Class Methods
    def __init__(self, shorthand='', **kwargs):
        kwargs['shorthand'] = shorthand
        kwds = dict()
        kwargs.update({k:v for k, v in kwds.items() if v is not jst.undefined})
        super(ConditionalText, self).__init__(**kwargs)

    def _finalize(self, **kwargs):
        """Finalize object: this involves inferring types if necessary"""
        # parse the shorthand to extract the field, type, and aggregate
        for key, val in parse_shorthand(self.shorthand).items():
            setattr(self, key, val)

        # infer the type if not already specified
        if self.type is jst.undefined:
            data = kwargs.get('data', jst.undefined)
            if isinstance(data, pd.DataFrame) and self.field in data:
                self.type = infer_vegalite_type(data[self.field])

        super(ConditionalText, self)._finalize(**kwargs)


class FacetField(schema.FacetFieldDef):
    """Wrapper for Vega-Lite FacetFieldDef definition.
    
    Attributes
    ----------
    shorthand: Unicode
        A shorthand description of the channel
    aggregate : object
        Aggregation function for the field
        (e.g., `mean`, `sum`, `median`, `min`, `max`, `count`).
        __Default value:__ `undefined` (None)
    bin : object
        Flag for binning a `quantitative` field, or a bin property
        object
        for binning parameters.
    field : object
        __Required.__ Name of the field from which to pull a data
        value.
        __Note:__ `field` is not required if `aggregate` is `count`.
    header : object
        
    timeUnit : object
        Time unit for a `temporal` field  (e.g., `year`, `yearmonth`,
        `month`, `hour`).
        __Default value:__ `undefined` (None)
    type : object
        The encoded field's type of measurement. This can be either a
        full type
        name (`"quantitative"`, `"temporal"`, `"ordinal"`,  and
        `"nominal"`)
        or an initial character of the type name (`"Q"`, `"T"`, `"O"`,
        `"N"`).
        This property is case-insensitive.
    """
    # Traitlets
    shorthand = jst.JSONString(default_value='', help="Shorthand specification of field, optionally including the aggregate and type (see :ref:`shorthand-description`)")
    _skip_on_export = ['shorthand']

    # Class Methods
    def __init__(self, shorthand='', aggregate=jst.undefined, bin=jst.undefined, field=jst.undefined, header=jst.undefined, timeUnit=jst.undefined, type=jst.undefined, **kwargs):
        kwargs['shorthand'] = shorthand
        kwds = dict(aggregate=aggregate, bin=bin, field=field, header=header, timeUnit=timeUnit, type=type)
        kwargs.update({k:v for k, v in kwds.items() if v is not jst.undefined})
        super(FacetField, self).__init__(**kwargs)

    def _finalize(self, **kwargs):
        """Finalize object: this involves inferring types if necessary"""
        # parse the shorthand to extract the field, type, and aggregate
        for key, val in parse_shorthand(self.shorthand).items():
            setattr(self, key, val)

        # infer the type if not already specified
        if self.type is jst.undefined:
            data = kwargs.get('data', jst.undefined)
            if isinstance(data, pd.DataFrame) and self.field in data:
                self.type = infer_vegalite_type(data[self.field])

        super(FacetField, self)._finalize(**kwargs)


class Field(schema.FieldDef):
    """Wrapper for Vega-Lite FieldDef definition.
    Definition object for a data field, its type and transformation of
    an encoding channel.
    Attributes
    ----------
    shorthand: Unicode
        A shorthand description of the channel
    aggregate : object
        Aggregation function for the field
        (e.g., `mean`, `sum`, `median`, `min`, `max`, `count`).
        __Default value:__ `undefined` (None)
    bin : object
        Flag for binning a `quantitative` field, or a bin property
        object
        for binning parameters.
    field : object
        __Required.__ Name of the field from which to pull a data
        value.
        __Note:__ `field` is not required if `aggregate` is `count`.
    timeUnit : object
        Time unit for a `temporal` field  (e.g., `year`, `yearmonth`,
        `month`, `hour`).
        __Default value:__ `undefined` (None)
    type : object
        The encoded field's type of measurement. This can be either a
        full type
        name (`"quantitative"`, `"temporal"`, `"ordinal"`,  and
        `"nominal"`)
        or an initial character of the type name (`"Q"`, `"T"`, `"O"`,
        `"N"`).
        This property is case-insensitive.
    """
    # Traitlets
    shorthand = jst.JSONString(default_value='', help="Shorthand specification of field, optionally including the aggregate and type (see :ref:`shorthand-description`)")
    _skip_on_export = ['shorthand']

    # Class Methods
    def __init__(self, shorthand='', aggregate=jst.undefined, bin=jst.undefined, field=jst.undefined, timeUnit=jst.undefined, type=jst.undefined, **kwargs):
        kwargs['shorthand'] = shorthand
        kwds = dict(aggregate=aggregate, bin=bin, field=field, timeUnit=timeUnit, type=type)
        kwargs.update({k:v for k, v in kwds.items() if v is not jst.undefined})
        super(Field, self).__init__(**kwargs)

    def _finalize(self, **kwargs):
        """Finalize object: this involves inferring types if necessary"""
        # parse the shorthand to extract the field, type, and aggregate
        for key, val in parse_shorthand(self.shorthand).items():
            setattr(self, key, val)

        # infer the type if not already specified
        if self.type is jst.undefined:
            data = kwargs.get('data', jst.undefined)
            if isinstance(data, pd.DataFrame) and self.field in data:
                self.type = infer_vegalite_type(data[self.field])

        super(Field, self)._finalize(**kwargs)


class OrderField(schema.OrderFieldDef):
    """Wrapper for Vega-Lite OrderFieldDef definition.
    
    Attributes
    ----------
    shorthand: Unicode
        A shorthand description of the channel
    aggregate : object
        Aggregation function for the field
        (e.g., `mean`, `sum`, `median`, `min`, `max`, `count`).
        __Default value:__ `undefined` (None)
    bin : object
        Flag for binning a `quantitative` field, or a bin property
        object
        for binning parameters.
    field : object
        __Required.__ Name of the field from which to pull a data
        value.
        __Note:__ `field` is not required if `aggregate` is `count`.
    sort : object
        
    timeUnit : object
        Time unit for a `temporal` field  (e.g., `year`, `yearmonth`,
        `month`, `hour`).
        __Default value:__ `undefined` (None)
    type : object
        The encoded field's type of measurement. This can be either a
        full type
        name (`"quantitative"`, `"temporal"`, `"ordinal"`,  and
        `"nominal"`)
        or an initial character of the type name (`"Q"`, `"T"`, `"O"`,
        `"N"`).
        This property is case-insensitive.
    """
    # Traitlets
    shorthand = jst.JSONString(default_value='', help="Shorthand specification of field, optionally including the aggregate and type (see :ref:`shorthand-description`)")
    _skip_on_export = ['shorthand']

    # Class Methods
    def __init__(self, shorthand='', aggregate=jst.undefined, bin=jst.undefined, field=jst.undefined, sort=jst.undefined, timeUnit=jst.undefined, type=jst.undefined, **kwargs):
        kwargs['shorthand'] = shorthand
        kwds = dict(aggregate=aggregate, bin=bin, field=field, sort=sort, timeUnit=timeUnit, type=type)
        kwargs.update({k:v for k, v in kwds.items() if v is not jst.undefined})
        super(OrderField, self).__init__(**kwargs)

    def _finalize(self, **kwargs):
        """Finalize object: this involves inferring types if necessary"""
        # parse the shorthand to extract the field, type, and aggregate
        for key, val in parse_shorthand(self.shorthand).items():
            setattr(self, key, val)

        # infer the type if not already specified
        if self.type is jst.undefined:
            data = kwargs.get('data', jst.undefined)
            if isinstance(data, pd.DataFrame) and self.field in data:
                self.type = infer_vegalite_type(data[self.field])

        super(OrderField, self)._finalize(**kwargs)


class PositionField(schema.PositionFieldDef):
    """Wrapper for Vega-Lite PositionFieldDef definition.
    
    Attributes
    ----------
    shorthand: Unicode
        A shorthand description of the channel
    aggregate : object
        Aggregation function for the field
        (e.g., `mean`, `sum`, `median`, `min`, `max`, `count`).
        __Default value:__ `undefined` (None)
    axis : object
        By default, Vega-Lite automatically creates axes for `x` and
        `y` channels when they are encoded.
        If `axis` is not defined, default axis properties are applied.
        User can provide set `axis` to an object to customize [axis
        properties](axis.html#axis-properties)
        or set `axis` to `null` to remove the axis.
    bin : object
        Flag for binning a `quantitative` field, or a bin property
        object
        for binning parameters.
    field : object
        __Required.__ Name of the field from which to pull a data
        value.
        __Note:__ `field` is not required if `aggregate` is `count`.
    scale : object
        
    sort : object
        Sort order for a field with discrete domain.
        This can be `"ascending"`, `"descending"`, `null`, or a [sort
        field definition object](sort.html#sort-field) for sorting by
        an aggregate calculation of a specified sort field.
        __Note:__ For fields with continuous domain, please use
        `"scale": {"reverse": true}` to flip the scale instead.
    stack : object
        Type of stacking offset if the field should be stacked.
        "none" or null, if the field should not be stacked.
    timeUnit : object
        Time unit for a `temporal` field  (e.g., `year`, `yearmonth`,
        `month`, `hour`).
        __Default value:__ `undefined` (None)
    type : object
        The encoded field's type of measurement. This can be either a
        full type
        name (`"quantitative"`, `"temporal"`, `"ordinal"`,  and
        `"nominal"`)
        or an initial character of the type name (`"Q"`, `"T"`, `"O"`,
        `"N"`).
        This property is case-insensitive.
    """
    # Traitlets
    shorthand = jst.JSONString(default_value='', help="Shorthand specification of field, optionally including the aggregate and type (see :ref:`shorthand-description`)")
    _skip_on_export = ['shorthand']

    # Class Methods
    def __init__(self, shorthand='', aggregate=jst.undefined, axis=jst.undefined, bin=jst.undefined, field=jst.undefined, scale=jst.undefined, sort=jst.undefined, stack=jst.undefined, timeUnit=jst.undefined, type=jst.undefined, **kwargs):
        kwargs['shorthand'] = shorthand
        kwds = dict(aggregate=aggregate, axis=axis, bin=bin, field=field, scale=scale, sort=sort, stack=stack, timeUnit=timeUnit, type=type)
        kwargs.update({k:v for k, v in kwds.items() if v is not jst.undefined})
        super(PositionField, self).__init__(**kwargs)

    def _finalize(self, **kwargs):
        """Finalize object: this involves inferring types if necessary"""
        # parse the shorthand to extract the field, type, and aggregate
        for key, val in parse_shorthand(self.shorthand).items():
            setattr(self, key, val)

        # infer the type if not already specified
        if self.type is jst.undefined:
            data = kwargs.get('data', jst.undefined)
            if isinstance(data, pd.DataFrame) and self.field in data:
                self.type = infer_vegalite_type(data[self.field])

        super(PositionField, self)._finalize(**kwargs)


