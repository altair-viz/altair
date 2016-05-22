"""
Main API for Vega-lite spec generation.

DSL mapping Vega types to IPython traitlets.
"""

try:
    import traitlets as T
except ImportError:
    from IPython.utils import traitlets as T

from .utils import (
    parse_shorthand, infer_vegalite_type,
    sanitize_dataframe, dataframe_to_json
)
from ._py3k_compat import string_types

import pandas as pd

from . import schema

from .schema import AggregateOp
from .schema import AxisConfig
from .schema import AxisOrient
from .schema import CellConfig
from .schema import Config
from .schema import DataFormat
from .schema import FacetConfig
from .schema import FacetGridConfig
from .schema import FacetScaleConfig
from .schema import FontStyle
from .schema import FontWeight
from .schema import HorizontalAlign
from .schema import LegendConfig
from .schema import MarkConfig
from .schema import NiceTime
from .schema import Scale
from .schema import ScaleConfig
from .schema import SortField
from .schema import SortOrder
from .schema import StackOffset
from .schema import TimeUnit
from .schema import Transform
from .schema import VerticalAlign
from .schema import Data

from .utils import INV_TYPECODE_MAP, TYPE_ABBR

#*************************************************************************
# Channels
#*************************************************************************


class _ChannelMixin(object):

    def _infer_type(self, data):
        if isinstance(data, pd.DataFrame):
            if not self.type and self.field in data:
                self.type = infer_vegalite_type(data[self.field])
        if data is None:
            self.type = ''

    def to_dict(self):
        if not self.field:
            return None
        if not self.type:
            raise ValueError("No vegalite data type defined for {0}".format(self.field))
        return super(_ChannelMixin, self).to_dict()


class PositionChannelDef(_ChannelMixin, schema.PositionChannelDef):

    skip = ['shorthand']

    shorthand = T.Unicode('')
    type = T.Union([schema.Type(), T.Unicode()],
                   allow_none=True, default_value=None)

    def __init__(self, shorthand, **kwargs):
        kwargs['shorthand'] = shorthand
        super(PositionChannelDef, self).__init__(**kwargs)

    @T.observe('shorthand')
    def _shorthand_changed(self, change):
        D = parse_shorthand(change['new'])
        for key, val in D.items():
            setattr(self, key, val)

    @T.observe('type')
    def _type_changed(self, change):
        new = change['new']
        if new in TYPE_ABBR:
            self.type = INV_TYPECODE_MAP[new]


class X(PositionChannelDef):
    channel_name = 'x'


class Y(PositionChannelDef):
    channel_name = 'y'


class Row(PositionChannelDef):
    channel_name = 'row'


class Column(PositionChannelDef):
    channel_name = 'column'


class ChannelDefWithLegend(_ChannelMixin, schema.ChannelDefWithLegend):

    skip = ['shorthand']

    shorthand = T.Unicode('')
    type = T.Union([schema.Type(), T.Unicode()],
                   allow_none=True, default_value=None)

    def __init__(self, shorthand, **kwargs):
        kwargs['shorthand'] = shorthand
        super(ChannelDefWithLegend, self).__init__(**kwargs)

    @T.observe('shorthand')
    def _shorthand_changed(self, change):
        D = parse_shorthand(change['new'])
        for key, val in D.items():
            setattr(self, key, val)

    @T.observe('type')
    def _type_changed(self, change):
        new = change['new']
        if new in TYPE_ABBR:
            self.type = INV_TYPECODE_MAP[new]


class Color(ChannelDefWithLegend):
    channel_name = 'color'


class Size(ChannelDefWithLegend):
    channel_name = 'size'


class Shape(ChannelDefWithLegend):
    channel_name = 'shape'


class Field(_ChannelMixin, schema.FieldDef):

    skip = ['shorthand']

    shorthand = T.Unicode('')
    type = T.Union([schema.Type(), T.Unicode()],
                   allow_none=True, default_value=None)

    def __init__(self, shorthand, **kwargs):
        kwargs['shorthand'] = shorthand
        super(Field, self).__init__(**kwargs)

    @T.observe('shorthand')
    def _shorthand_changed(self, change):
        D = parse_shorthand(change['new'])
        for key, val in D.items():
            setattr(self, key, val)

    @T.observe('type')
    def _type_changed(self, change):
        new = change['new']
        if new in TYPE_ABBR:
            self.type = INV_TYPECODE_MAP[new]


class Text(Field):
    channel_name = 'text'


class Label(Field):
    channel_name = 'label'


class Detail(Field):
    channel_name = 'detail'


class OrderChannel(_ChannelMixin, schema.OrderChannelDef):

    skip = ['shorthand']

    shorthand = T.Unicode('')
    type = T.Union([schema.Type(), T.Unicode()],
                   allow_none=True, default_value=None)

    def __init__(self, shorthand, **kwargs):
        kwargs['shorthand'] = shorthand
        super(OrderChannel, self).__init__(**kwargs)

    @T.observe('shorthand')
    def _shorthand_changed(self, change):
        D = parse_shorthand(change['new'])
        for key, val in D.items():
            setattr(self, key, val)

    @T.observe('type')
    def _type_changed(self, change):
        new = change['new']
        if new in TYPE_ABBR:
            self.type = INV_TYPECODE_MAP[new]


class Order(OrderChannel):
    channel_name = 'order'


class Path(OrderChannel):
    channel_name = 'path'


#*************************************************************************
# Aliases
#*************************************************************************


class Axis(schema.AxisProperties):
    pass


class Bin(schema.BinProperties):
    pass


class Legend(schema.LegendProperties):
    pass


class Formula(schema.VgFormula):

    def __init__(self, field, **kwargs):
        kwargs['field'] = field
        super(Formula, self).__init__(**kwargs)


#*************************************************************************
# Encoding
#*************************************************************************


CHANNEL_CLASSES = {
    'x': X,
    'y': Y,
    'row': Row,
    'column': Column,
    'color': Color,
    'size': Size,
    'shape': Shape,
    'detail': Detail,
    'text': Text,
    'label': Label,
    'path': Path,
    'order': Order

}

CHANNEL_NAMES = list(CHANNEL_CLASSES.keys())

MARK_TYPES = [
    "area",
    "bar",
    "line",
    "point",
    "text",
    "tick",
    "circle",
    "square"
]


class Encoding(schema.Encoding):

    # Position channels
    x = T.Instance(X, default_value=None, allow_none=True)
    y = T.Instance(Y, default_value=None, allow_none=True)
    row = T.Instance(Row, default_value=None, allow_none=True)
    column = T.Instance(Column, default_value=None, allow_none=True)

    # Channels with legends
    color = T.Instance(Color, default_value=None, allow_none=True)
    size = T.Instance(Size, default_value=None, allow_none=True)
    shape = T.Instance(Shape, default_value=None, allow_none=True)

    # Field and order channels
    detail = T.Union([T.Instance(Detail), T.List(T.Instance(Detail))],
                     default_value=None, allow_none=True)
    text = T.Instance(Text, default_value=None, allow_none=True)
    label = T.Instance(Label, default_value=None, allow_none=True)
    path = T.Union([T.Instance(Path), T.List(T.Instance(Path))],
                   default_value=None, allow_none=True)
    order = T.Union([T.Instance(Order), T.List(T.Instance(Order))],
                   default_value=None, allow_none=True)

    parent = T.Instance(schema.BaseObject, default_value=None, allow_none=True)

    skip = ['parent']

    def _infer_types(self, data):
        for attr in CHANNEL_NAMES:
            val = getattr(self, attr)
            if val is not None:
                val._infer_type(data)

    @T.observe(*CHANNEL_NAMES)
    def _channel_changed(self, change):
        new = change['new']
        name = change['name']
        channel = getattr(self, name, None)
        if channel is not None and not getattr(channel, 'type', '') and isinstance(self.parent, Layer):
            meth = getattr(channel, '_infer_type', None)
            if meth is not None:
                meth(self.parent.data)


#*************************************************************************
# Encoding
#*************************************************************************


class Layer(schema.BaseObject):

    _data = None

    name = T.Unicode()
    description = T.Unicode()
    transform = T.Instance(schema.Transform, default_value=None, allow_none=True)
    mark = T.Enum(MARK_TYPES, default_value='point')
    encoding = T.Instance(Encoding, default_value=None, allow_none=True)
    config = T.Instance(schema.Config, allow_none=True)

    def _encoding_changed(self, name, old, new):
        if isinstance(new, Encoding):
            self.encoding.parent = self
            if isinstance(self.data, pd.DataFrame):
                self.encoding._infer_types(self.data)

    def _set_data(self, new):
        if not (isinstance(new, pd.DataFrame) or isinstance(new, Data) or new is None):
            raise TypeError('Expected DataFrame or altair.Data, got: {0}'.format(new))
        if self.encoding is not None:
            self.encoding._infer_types(new)
        self._data = new

    def _get_data(self):
        return self._data

    data = property(_get_data, _set_data)

    skip = ['data', '_data']

    def __init__(self, *args, **kwargs):
        super(Layer, self).__init__(**kwargs)
        if len(args)==1:
            self.data = args[0]

    def __dir__(self):
        base = super(Layer, self).__dir__()
        methods = [
            'encode', 'configure', 'display',
            'mark_area', 'mark_bar', 'mark_line', 'mark_point',
            'mark_text', 'mark_tick', 'mark_circle', 'mark_square'
        ]
        print(base, methods)
        return base+methods

    def to_dict(self, data=True):
        D = super(Layer, self).to_dict()
        if data:
            if isinstance(self.data, Data):
                D['data'] = self.data.to_dict()
            if isinstance(self.data, pd.DataFrame):
                values = sanitize_dataframe(self.data).to_dict(orient='records')
                D['data'] = Data(values=values).to_dict()
        else:
            D.pop('data', None)
        return D

    def encode(self, *args, **kwargs):
        """Define the encoding for the Layer."""
        for key, val in kwargs.items():
            if key in CHANNEL_CLASSES:
                if not isinstance(val, CHANNEL_CLASSES[key]):
                    kwargs[key] = CHANNEL_CLASSES[key](val)
        for item in args:
            if item.channel_name in kwargs:
                raise ValueError('Mulitple value for {0} provided'.format(item.channel_name))
            kwargs[item.channel_name] = item
        if self.encoding is None:
            self.encoding = Encoding()
        self.encoding.update_traits(**kwargs)
        return self

    def configure(self, *args, **kwargs):
        """Set chart configuration"""
        # Map config trait names to their classes
        name_to_trait = {key: val.klass
                         for key, val in schema.Config.class_traits().items()
                         if isinstance(val, T.Instance)}
        trait_to_name = {v:k for k, v in name_to_trait.items()}

        if len(name_to_trait) != len(trait_to_name):
            raise ValueError("Two Config() traits have the same class. "
                             "(Possibly caused by a vega-lite schema update?)")

        for val in args:
            if val.__class__ in trait_to_name:
                key = trait_to_name[val.__class__]
                if key in kwargs:
                    raise ValueError("{0} specified twice".format(key))
                kwargs[key] = val
            else:
                raise ValueError("unrecognized argument: {0}".format(val))
        if self.config is None:
            self.config = schema.Config()
        self.config.update_traits(**kwargs)
        return self

    def transform_data(self, **kwargs):
        """Set the Data Transform"""
        if self.transform is None:
            self.transform = schema.Transform()
        self.transform.update_traits(**kwargs)
        return self

    def mark_area(self, **kwargs):
        self.mark = 'area'
        if kwargs:
            self.configure(MarkConfig(**kwargs))
        return self

    def mark_bar(self, **kwargs):
        self.mark = 'bar'
        if kwargs:
            self.configure(MarkConfig(**kwargs))
        return self

    def mark_line(self, **kwargs):
        self.mark = 'line'
        if kwargs:
            self.configure(MarkConfig(**kwargs))
        return self

    def mark_point(self, **kwargs):
        self.mark = 'point'
        if kwargs:
            self.configure(MarkConfig(**kwargs))
        return self

    def mark_text(self, **kwargs):
        self.mark = 'text'
        if kwargs:
            self.configure(MarkConfig(**kwargs))
        return self

    def mark_tick(self, **kwargs):
        self.mark = 'tick'
        if kwargs:
            self.configure(MarkConfig(**kwargs))
        return self

    def mark_circle(self, **kwargs):
        self.mark = 'circle'
        if kwargs:
            self.configure(MarkConfig(**kwargs))
        return self

    def mark_square(self, **kwargs):
        self.mark = 'square'
        if kwargs:
            self.configure(MarkConfig(**kwargs))
        return self

    def _ipython_display_(self):
        from IPython.display import display
        from vega import VegaLite
        display(VegaLite(self.to_dict()))

    def display(self):
        from IPython.display import display
        display(self)
