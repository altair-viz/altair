from .core import (
    infer_vegalite_type_for_pandas,
    infer_encoding_types,
    sanitize_pandas_dataframe,
    sanitize_narwhals_dataframe,
    parse_shorthand,
    use_signature,
    update_nested,
    display_traceback,
    SchemaBase,
)
from .html import spec_to_html
from .plugin_registry import PluginRegistry
from .deprecation import AltairDeprecationWarning
from .schemapi import Undefined, Optional


__all__ = (
    "AltairDeprecationWarning",
    "Optional",
    "PluginRegistry",
    "SchemaBase",
    "Undefined",
    "display_traceback",
    "infer_encoding_types",
    "infer_vegalite_type_for_pandas",
    "parse_shorthand",
    "sanitize_narwhals_dataframe",
    "sanitize_pandas_dataframe",
    "spec_to_html",
    "update_nested",
    "use_signature",
)
