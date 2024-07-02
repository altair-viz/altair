"""Generate a schema wrapper from a schema"""

from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
import re
import sys
import textwrap
from dataclasses import dataclass
from typing import Final, Iterable, Literal
from urllib import request
import m2r

sys.path.insert(0, str(Path.cwd()))
from tools.schemapi import codegen, CodeSnippet, SchemaInfo
from tools.schemapi.utils import (
    get_valid_identifier,
    resolve_references,
    ruff_format_py,
    rst_syntax_for_class,
    indent_docstring,
    ruff_write_lint_format_str,
)


SCHEMA_VERSION: Final = "v5.17.0"

reLink = re.compile(r"(?<=\[)([^\]]+)(?=\]\([^\)]+\))", re.MULTILINE)
reSpecial = re.compile(r"[*_]{2,3}|`", re.MULTILINE)

HEADER: Final = """\
# The contents of this file are automatically written by
# tools/generate_schema_wrapper.py. Do not modify directly.
"""

SCHEMA_URL_TEMPLATE: Final = "https://vega.github.io/schema/{library}/{version}.json"

CHANNEL_MYPY_IGNORE_STATEMENTS: Final = """\
# These errors need to be ignored as they come from the overload methods
# which trigger two kind of errors in mypy:
# * all of them do not have an implementation in this file
# * some of them are the only overload methods -> overloads usually only make
#   sense if there are multiple ones
# However, we need these overloads due to how the propertysetter works
# mypy: disable-error-code="no-overload-impl, empty-body, misc"
"""

BASE_SCHEMA: Final = """
class {basename}(SchemaBase):
    _rootschema = load_schema()
    @classmethod
    def _default_wrapper_classes(cls) -> Iterator[type[Any]]:
        return _subclasses({basename})
"""

LOAD_SCHEMA: Final = '''
def load_schema() -> dict:
    """Load the json schema associated with this module's functions"""
    schema_bytes = pkgutil.get_data(__name__, "{schemafile}")
    if schema_bytes is None:
        raise ValueError("Unable to load {schemafile}")
    return json.loads(
        schema_bytes.decode("utf-8")
    )
'''


CHANNEL_MIXINS: Final = """
class FieldChannelMixin:
    _encoding_name: str
    def to_dict(
        self,
        validate: bool = True,
        ignore: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict | list[dict]:
        context = context or {}
        ignore = ignore or []
        shorthand = self._get("shorthand")  # type: ignore[attr-defined]
        field = self._get("field")  # type: ignore[attr-defined]

        if shorthand is not Undefined and field is not Undefined:
            msg = f"{self.__class__.__name__} specifies both shorthand={shorthand} and field={field}. "
            raise ValueError(msg)

        if isinstance(shorthand, (tuple, list)):
            # If given a list of shorthands, then transform it to a list of classes
            kwds = self._kwds.copy()  # type: ignore[attr-defined]
            kwds.pop("shorthand")
            return [
                self.__class__(sh, **kwds).to_dict(  # type: ignore[call-arg]
                    validate=validate, ignore=ignore, context=context
                )
                for sh in shorthand
            ]

        if shorthand is Undefined:
            parsed = {}
        elif isinstance(shorthand, str):
            parsed = parse_shorthand(shorthand, data=context.get("data", None))
            type_required = "type" in self._kwds  # type: ignore[attr-defined]
            type_in_shorthand = "type" in parsed
            type_defined_explicitly = self._get("type") is not Undefined  # type: ignore[attr-defined]
            if not type_required:
                # Secondary field names don't require a type argument in VegaLite 3+.
                # We still parse it out of the shorthand, but drop it here.
                parsed.pop("type", None)
            elif not (type_in_shorthand or type_defined_explicitly):
                if _is_pandas_dataframe(context.get("data", None)):
                    msg = (
                        f'Unable to determine data type for the field "{shorthand}";'
                        " verify that the field name is not misspelled."
                        " If you are referencing a field from a transform,"
                        " also confirm that the data type is specified correctly."
                    )
                    raise ValueError(msg)
                else:
                    msg = (
                        f"{shorthand} encoding field is specified without a type; "
                        "the type cannot be automatically inferred because "
                        "the data is not specified as a pandas.DataFrame."
                    )
                    raise ValueError(msg)
        else:
            # Shorthand is not a string; we pass the definition to field,
            # and do not do any parsing.
            parsed = {"field": shorthand}
        context["parsed_shorthand"] = parsed

        return super(FieldChannelMixin, self).to_dict(
            validate=validate, ignore=ignore, context=context
        )


class ValueChannelMixin:
    _encoding_name: str
    def to_dict(
        self,
        validate: bool = True,
        ignore: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict:
        context = context or {}
        ignore = ignore or []
        condition = self._get("condition", Undefined)  # type: ignore[attr-defined]
        copy = self  # don't copy unless we need to
        if condition is not Undefined:
            if isinstance(condition, core.SchemaBase):
                pass
            elif "field" in condition and "type" not in condition:
                kwds = parse_shorthand(condition["field"], context.get("data", None))
                copy = self.copy(deep=["condition"])  # type: ignore[attr-defined]
                copy["condition"].update(kwds)  # type: ignore[index]
        return super(ValueChannelMixin, copy).to_dict(
            validate=validate, ignore=ignore, context=context
        )


class DatumChannelMixin:
    _encoding_name: str
    def to_dict(
        self,
        validate: bool = True,
        ignore: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict:
        context = context or {}
        ignore = ignore or []
        datum = self._get("datum", Undefined)  # type: ignore[attr-defined] # noqa
        copy = self  # don't copy unless we need to
        return super(DatumChannelMixin, copy).to_dict(
            validate=validate, ignore=ignore, context=context
        )
"""

MARK_METHOD: Final = '''
def mark_{mark}({def_arglist}) -> Self:
    """Set the chart's mark to '{mark}' (see :class:`{mark_def}`)
    """
    kwds = dict({dict_arglist})
    copy = self.copy(deep=False)  # type: ignore[attr-defined]
    if any(val is not Undefined for val in kwds.values()):
        copy.mark = core.{mark_def}(type="{mark}", **kwds)
    else:
        copy.mark = "{mark}"
    return copy
'''

CONFIG_METHOD: Final = """
@use_signature(core.{classname})
def {method}(self, *args, **kwargs) -> Self:
    copy = self.copy(deep=False)  # type: ignore[attr-defined]
    copy.config = core.{classname}(*args, **kwargs)
    return copy
"""

CONFIG_PROP_METHOD: Final = """
@use_signature(core.{classname})
def configure_{prop}(self, *args, **kwargs) -> Self:
    copy = self.copy(deep=['config'])  # type: ignore[attr-defined]
    if copy.config is Undefined:
        copy.config = core.Config()
    copy.config["{prop}"] = core.{classname}(*args, **kwargs)
    return copy
"""

ENCODE_METHOD: Final = '''
class _EncodingMixin:
    def encode({encode_method_args}) -> Self:
        """Map properties of the data to visual properties of the chart (see :class:`FacetedEncoding`)
        {docstring}"""
        # Compat prep for `infer_encoding_types` signature
        kwargs = locals()
        kwargs.pop("self")
        args = kwargs.pop("args")
        if args:
            kwargs = {{k: v for k, v in kwargs.items() if v is not Undefined}}

        # Convert args to kwargs based on their types.
        kwargs = _infer_encoding_types(args, kwargs)
        # get a copy of the dict representation of the previous encoding
        # ignore type as copy method comes from SchemaBase
        copy = self.copy(deep=['encoding'])  # type: ignore[attr-defined]
        encoding = copy._get('encoding', {{}})
        if isinstance(encoding, core.VegaLiteSchema):
            encoding = {{k: v for k, v in encoding._kwds.items() if v is not Undefined}}
        # update with the new encodings, and apply them to the copy
        encoding.update(kwargs)
        copy.encoding = core.FacetedEncoding(**encoding)
        return copy
'''

# These types should support annotations in generated code,
# but are not derived from the schema itself.
EXTRA_ALIASES: Final = """
Map: TypeAlias = Mapping[str, Any]
"""


class SchemaGenerator(codegen.SchemaGenerator):
    schema_class_template = textwrap.dedent(
        '''
    class {classname}({basename}):
        """{docstring}"""
        _schema = {schema!r}

        {init_code}
    '''
    )

    @staticmethod
    def _process_description(description: str) -> str:
        return process_description(description)


def process_description(description: str) -> str:
    description = "".join(
        [
            reSpecial.sub("", d) if i % 2 else d
            for i, d in enumerate(reLink.split(description))
        ]
    )  # remove formatting from links
    description = m2r.convert(description)
    description = description.replace(m2r.prolog, "")
    description = description.replace(":raw-html-m2r:", ":raw-html:")
    description = description.replace(r"\ ,", ",")
    description = description.replace(r"\ ", " ")
    # turn explicit references into anonymous references
    description = description.replace(">`_", ">`__")
    # Some entries in the Vega-Lite schema miss the second occurence of '__'
    description = description.replace("__Default value: ", "__Default value:__ ")
    # Fixing ambiguous unicode, RUF001 produces RUF002 in docs
    description = description.replace("’", "'")  # noqa: RUF001 [RIGHT SINGLE QUOTATION MARK]
    description = description.replace("–", "-")  # noqa: RUF001 [EN DASH]
    description = description.replace(" ", " ")  # noqa: RUF001 [NO-BREAK SPACE]
    description += "\n"
    return description.strip()


class FieldSchemaGenerator(SchemaGenerator):
    schema_class_template = textwrap.dedent(
        '''
    @with_property_setters
    class {classname}(FieldChannelMixin, core.{basename}):
        """{docstring}"""
        _class_is_valid_at_instantiation = False
        _encoding_name = "{encodingname}"

        {method_code}

        {init_code}
    '''
    )


class ValueSchemaGenerator(SchemaGenerator):
    schema_class_template = textwrap.dedent(
        '''
    @with_property_setters
    class {classname}(ValueChannelMixin, core.{basename}):
        """{docstring}"""
        _class_is_valid_at_instantiation = False
        _encoding_name = "{encodingname}"

        {method_code}

        {init_code}
    '''
    )


class DatumSchemaGenerator(SchemaGenerator):
    schema_class_template = textwrap.dedent(
        '''
    @with_property_setters
    class {classname}(DatumChannelMixin, core.{basename}):
        """{docstring}"""
        _class_is_valid_at_instantiation = False
        _encoding_name = "{encodingname}"

        {method_code}

        {init_code}
    '''
    )


def schema_class(*args, **kwargs) -> str:
    return SchemaGenerator(*args, **kwargs).schema_class()


def schema_url(version: str = SCHEMA_VERSION) -> str:
    return SCHEMA_URL_TEMPLATE.format(library="vega-lite", version=version)


def download_schemafile(
    version: str, schemapath: Path, skip_download: bool = False
) -> Path:
    url = schema_url(version=version)
    schemadir = Path(schemapath)
    schemadir.mkdir(parents=True, exist_ok=True)
    fp = schemadir / "vega-lite-schema.json"
    if not skip_download:
        request.urlretrieve(url, fp)
    elif not fp.exists():
        msg = f"Cannot skip download: {fp!s} does not exist"
        raise ValueError(msg)
    return fp


def load_schema_with_shorthand_properties(schemapath: Path) -> dict:
    with schemapath.open(encoding="utf8") as f:
        schema = json.load(f)

    schema = _add_shorthand_property_to_field_encodings(schema)
    return schema


def _add_shorthand_property_to_field_encodings(schema: dict) -> dict:
    encoding_def = "FacetedEncoding"

    encoding = SchemaInfo(schema["definitions"][encoding_def], rootschema=schema)

    for _, propschema in encoding.properties.items():
        def_dict = get_field_datum_value_defs(propschema, schema)

        field_ref = def_dict.get("field")
        if field_ref is not None:
            defschema = {"$ref": field_ref}
            defschema = copy.deepcopy(resolve_references(defschema, schema))
            # For Encoding field definitions, we patch the schema by adding the
            # shorthand property.
            defschema["properties"]["shorthand"] = {
                "anyOf": [
                    {"type": "string"},
                    {"type": "array", "items": {"type": "string"}},
                    {"$ref": "#/definitions/RepeatRef"},
                ],
                "description": "shorthand for field, aggregate, and type",
            }
            if "required" not in defschema:
                defschema["required"] = ["shorthand"]
            elif "shorthand" not in defschema["required"]:
                defschema["required"].append("shorthand")
            schema["definitions"][field_ref.split("/")[-1]] = defschema
    return schema


def copy_schemapi_util() -> None:
    """
    Copy the schemapi utility into altair/utils/ and its test file to tests/utils/
    """
    # copy the schemapi utility file
    source_fp = Path(__file__).parent / "schemapi" / "schemapi.py"
    destination_fp = Path(__file__).parent / ".." / "altair" / "utils" / "schemapi.py"

    print(f"Copying\n {source_fp!s}\n  -> {destination_fp!s}")
    with source_fp.open(encoding="utf8") as source, destination_fp.open(
        "w", encoding="utf8"
    ) as dest:
        dest.write(HEADER)
        dest.writelines(source.readlines())
    if sys.platform == "win32":
        ruff_format_py(destination_fp)


def recursive_dict_update(schema: dict, root: dict, def_dict: dict) -> None:
    if "$ref" in schema:
        next_schema = resolve_references(schema, root)
        if "properties" in next_schema:
            definition = schema["$ref"]
            properties = next_schema["properties"]
            for k in def_dict:
                if k in properties:
                    def_dict[k] = definition
        else:
            recursive_dict_update(next_schema, root, def_dict)
    elif "anyOf" in schema:
        for sub_schema in schema["anyOf"]:
            recursive_dict_update(sub_schema, root, def_dict)


def get_field_datum_value_defs(propschema: SchemaInfo, root: dict) -> dict[str, str]:
    def_dict: dict[str, str | None] = dict.fromkeys(("field", "datum", "value"))
    schema = propschema.schema
    if propschema.is_reference() and "properties" in schema:
        if "field" in schema["properties"]:
            def_dict["field"] = propschema.ref
        else:
            msg = "Unexpected schema structure"
            raise ValueError(msg)
    else:
        recursive_dict_update(schema, root, def_dict)

    return {i: j for i, j in def_dict.items() if j}


def toposort(graph: dict[str, list[str]]) -> list[str]:
    """Topological sort of a directed acyclic graph.

    Parameters
    ----------
    graph : dict of lists
        Mapping of node labels to list of child node labels.
        This is assumed to represent a graph with no cycles.

    Returns
    -------
    order : list
        topological order of input graph.
    """
    # Once we drop support for Python 3.8, this can potentially be replaced
    # with graphlib.TopologicalSorter from the standard library.
    stack: list[str] = []
    visited: dict[str, Literal[True]] = {}

    def visit(nodes):
        for node in sorted(nodes, reverse=True):
            if not visited.get(node):
                visited[node] = True
                visit(graph.get(node, []))
                stack.insert(0, node)

    visit(graph)
    return stack


def generate_vegalite_schema_wrapper(schema_file: Path) -> str:
    """Generate a schema wrapper at the given path."""
    # TODO: generate simple tests for each wrapper
    basename = "VegaLiteSchema"

    rootschema = load_schema_with_shorthand_properties(schema_file)

    definitions: dict[str, SchemaGenerator] = {}

    for name in rootschema["definitions"]:
        defschema = {"$ref": "#/definitions/" + name}
        defschema_repr = {"$ref": "#/definitions/" + name}
        name = get_valid_identifier(name)
        definitions[name] = SchemaGenerator(
            name,
            schema=defschema,
            schemarepr=defschema_repr,
            rootschema=rootschema,
            basename=basename,
            rootschemarepr=CodeSnippet(f"{basename}._rootschema"),
        )

    graph: dict[str, list[str]] = {}

    for name, schema in definitions.items():
        graph[name] = []
        for child_name in schema.subclasses():
            child_name = get_valid_identifier(child_name)
            graph[name].append(child_name)
            child: SchemaGenerator = definitions[child_name]
            if child.basename == basename:
                child.basename = [name]
            else:
                assert isinstance(child.basename, list)
                child.basename.append(name)

    # Specify __all__ explicitly so that we can exclude the ones from the list
    # of exported classes which are also defined in the channels or api modules which takes
    # precedent in the generated __init__.py files one and two levels up.
    # Importing these classes from multiple modules confuses type checkers.
    it = (
        c
        for c in definitions.keys() - {"Color", "Text", "LookupData"}
        if not c.startswith("_")
    )
    all_ = [*sorted(it), "Root", "VegaLiteSchema", "SchemaBase", "load_schema"]

    contents = [
        HEADER,
        "from __future__ import annotations\n"
        "from typing import Any, Literal, Union, Protocol, Sequence, List, Iterator, TYPE_CHECKING",
        "import pkgutil",
        "import json\n",
        "from narwhals.dependencies import is_pandas_dataframe as _is_pandas_dataframe",
        "from altair.utils.schemapi import SchemaBase, Undefined, UndefinedType, _subclasses # noqa: F401\n",
        _type_checking_only_imports(
            "from altair import Parameter",
            "from altair.utils.schemapi import Optional",
            "from ._typing import * # noqa: F403",
        ),
        "\n" f"__all__ = {all_}\n",
        LOAD_SCHEMA.format(schemafile="vega-lite-schema.json"),
        BASE_SCHEMA.format(basename=basename),
        schema_class(
            "Root",
            schema=rootschema,
            basename=basename,
            schemarepr=CodeSnippet(f"{basename}._rootschema"),
        ),
    ]

    for name in toposort(graph):
        contents.append(definitions[name].schema_class())

    contents.append("")  # end with newline
    return "\n".join(contents)


def _type_checking_only_imports(*imports: str) -> str:
    return (
        "\n# ruff: noqa: F405\nif TYPE_CHECKING:\n"
        + "\n".join(f"    {s}" for s in imports)
        + "\n"
    )


@dataclass
class ChannelInfo:
    supports_arrays: bool
    deep_description: str
    field_class_name: str | None = None
    datum_class_name: str | None = None
    value_class_name: str | None = None


def generate_vegalite_channel_wrappers(
    schemafile: Path, version: str, imports: list[str] | None = None
) -> str:
    # TODO: generate __all__ for top of file
    schema = load_schema_with_shorthand_properties(schemafile)

    imports = imports or [
        "from __future__ import annotations\n",
        "from typing import Any, overload, Sequence, List, Literal, Union, TYPE_CHECKING",
        "from narwhals.dependencies import is_pandas_dataframe as _is_pandas_dataframe",
        "from altair.utils.schemapi import Undefined, with_property_setters",
        "from altair.utils import infer_encoding_types as _infer_encoding_types",
        "from altair.utils import parse_shorthand",
        "from . import core",
    ]
    contents = [
        HEADER,
        CHANNEL_MYPY_IGNORE_STATEMENTS,
        *imports,
        _type_checking_only_imports(
            "from altair import Parameter, SchemaBase",
            "from altair.utils.schemapi import Optional",
            "from ._typing import * # noqa: F403",
            "from typing_extensions import Self",
        ),
        CHANNEL_MIXINS,
    ]

    encoding_def = "FacetedEncoding"

    encoding = SchemaInfo(schema["definitions"][encoding_def], rootschema=schema)

    channel_infos: dict[str, ChannelInfo] = {}

    for prop, propschema in encoding.properties.items():
        def_dict = get_field_datum_value_defs(propschema, schema)

        supports_arrays = any(
            schema_info.is_array() for schema_info in propschema.anyOf
        )
        channel_info = ChannelInfo(
            supports_arrays=supports_arrays,
            deep_description=propschema.deep_description,
        )

        for encoding_spec, definition in def_dict.items():
            classname = prop[0].upper() + prop[1:]
            basename = definition.rsplit("/", maxsplit=1)[-1]
            basename = get_valid_identifier(basename)

            defschema = {"$ref": definition}

            Generator: (
                type[FieldSchemaGenerator]
                | type[DatumSchemaGenerator]
                | type[ValueSchemaGenerator]
            )
            if encoding_spec == "field":
                Generator = FieldSchemaGenerator
                nodefault = []
                channel_info.field_class_name = classname

            elif encoding_spec == "datum":
                Generator = DatumSchemaGenerator
                classname += "Datum"
                nodefault = ["datum"]
                channel_info.datum_class_name = classname

            elif encoding_spec == "value":
                Generator = ValueSchemaGenerator
                classname += "Value"
                nodefault = ["value"]
                channel_info.value_class_name = classname

            gen = Generator(
                classname=classname,
                basename=basename,
                schema=defschema,
                rootschema=schema,
                encodingname=prop,
                nodefault=nodefault,
                haspropsetters=True,
                altair_classes_prefix="core",
            )
            contents.append(gen.schema_class())

        channel_infos[prop] = channel_info

    # Generate the type signature for the encode method
    encode_signature = _create_encode_signature(channel_infos)
    contents.append(encode_signature)
    return "\n".join(contents)


def generate_vegalite_mark_mixin(
    schemafile: Path, markdefs: dict[str, str]
) -> tuple[list[str], str]:
    with schemafile.open(encoding="utf8") as f:
        schema = json.load(f)

    class_name = "MarkMethodMixin"

    imports = [
        "from typing import Any, Sequence, List, Literal, Union",
        "",
        "from altair.utils.schemapi import Undefined, UndefinedType",
        "from . import core",
    ]

    code = [
        f"class {class_name}:",
        '    """A mixin class that defines mark methods"""',
    ]

    for mark_enum, mark_def in markdefs.items():
        if "enum" in schema["definitions"][mark_enum]:
            marks = schema["definitions"][mark_enum]["enum"]
        else:
            marks = [schema["definitions"][mark_enum]["const"]]
        info = SchemaInfo({"$ref": f"#/definitions/{mark_def}"}, rootschema=schema)

        # adapted from SchemaInfo.init_code
        arg_info = codegen.get_args(info)
        arg_info.required -= {"type"}
        arg_info.kwds -= {"type"}

        def_args = ["self"] + [
            f"{p}: "
            + info.properties[p].get_python_type_representation(
                for_type_hints=True,
                additional_type_hints=["UndefinedType"],
            )
            + " = Undefined"
            for p in (sorted(arg_info.required) + sorted(arg_info.kwds))
        ]
        dict_args = [
            f"{p}={p}" for p in (sorted(arg_info.required) + sorted(arg_info.kwds))
        ]

        if arg_info.additional or arg_info.invalid_kwds:
            def_args.append("**kwds")
            dict_args.append("**kwds")

        for mark in marks:
            # TODO: only include args relevant to given type?
            mark_method = MARK_METHOD.format(
                mark=mark,
                mark_def=mark_def,
                def_arglist=", ".join(def_args),
                dict_arglist=", ".join(dict_args),
            )
            code.append("\n    ".join(mark_method.splitlines()))

    return imports, "\n".join(code)


def generate_vegalite_config_mixin(schemafile: Path) -> tuple[list[str], str]:
    imports = [
        "from . import core",
        "from altair.utils import use_signature",
    ]

    class_name = "ConfigMethodMixin"

    code = [
        f"class {class_name}:",
        '    """A mixin class that defines config methods"""',
    ]
    with schemafile.open(encoding="utf8") as f:
        schema = json.load(f)
    info = SchemaInfo({"$ref": "#/definitions/Config"}, rootschema=schema)

    # configure() method
    method = CONFIG_METHOD.format(classname="Config", method="configure")
    code.append("\n    ".join(method.splitlines()))

    # configure_prop() methods
    for prop, prop_info in info.properties.items():
        classname = prop_info.refname
        if classname and classname.endswith("Config"):
            method = CONFIG_PROP_METHOD.format(classname=classname, prop=prop)
            code.append("\n    ".join(method.splitlines()))
    return imports, "\n".join(code)


def vegalite_main(skip_download: bool = False) -> None:
    version = SCHEMA_VERSION
    vn = version.split(".")[0]
    fp = (Path(__file__).parent / ".." / "altair" / "vegalite" / vn).resolve()
    schemapath = fp / "schema"
    schemafile = download_schemafile(
        version=version,
        schemapath=schemapath,
        skip_download=skip_download,
    )

    # Generate __init__.py file
    outfile = schemapath / "__init__.py"
    print(f"Writing {outfile!s}")
    content = [
        "# ruff: noqa\n",
        "from .core import *\nfrom .channels import *\n",
        f"SCHEMA_VERSION = '{version}'\n",
        f"SCHEMA_URL = {schema_url(version)!r}\n",
    ]
    ruff_write_lint_format_str(outfile, content)

    files: dict[Path, str | Iterable[str]] = {}

    # Generate the core schema wrappers
    fp_core = schemapath / "core.py"
    print(f"Generating\n {schemafile!s}\n  ->{fp_core!s}")
    files[fp_core] = generate_vegalite_schema_wrapper(schemafile)

    # Generate the channel wrappers
    fp_channels = schemapath / "channels.py"
    print(f"Generating\n {schemafile!s}\n  ->{fp_channels!s}")
    files[fp_channels] = generate_vegalite_channel_wrappers(schemafile, version=version)

    # generate the mark mixin
    markdefs = {k: f"{k}Def" for k in ["Mark", "BoxPlot", "ErrorBar", "ErrorBand"]}
    fp_mixins = schemapath / "mixins.py"
    print(f"Generating\n {schemafile!s}\n  ->{fp_mixins!s}")
    mark_imports, mark_mixin = generate_vegalite_mark_mixin(schemafile, markdefs)
    config_imports, config_mixin = generate_vegalite_config_mixin(schemafile)
    try_except_imports = [
        "if sys.version_info >= (3, 11):",
        "    from typing import Self",
        "else:",
        "    from typing_extensions import Self",
    ]
    stdlib_imports = ["from __future__ import annotations\n", "import sys"]
    content_mixins = [
        HEADER,
        "\n".join(stdlib_imports),
        "\n\n",
        "\n".join(sorted({*mark_imports, *config_imports})),
        "\n\n",
        "\n".join(try_except_imports),
        "\n\n",
        _type_checking_only_imports(
            "from altair import Parameter, SchemaBase",
            "from altair.utils.schemapi import Optional",
            "from ._typing import * # noqa: F403",
        ),
        "\n\n\n",
        mark_mixin,
        "\n\n\n",
        config_mixin,
    ]
    files[fp_mixins] = content_mixins

    # Write `_typing.py` TypeAlias, for import in generated modules
    from tools.schemapi.utils import TypeAliasTracer

    fp_typing = schemapath / "_typing.py"
    msg = (
        f"Generating\n {schemafile!s}\n  ->{fp_typing!s}\n"
        f"Tracer cache collected {TypeAliasTracer.n_entries!r} entries."
    )
    print(msg)
    TypeAliasTracer.write_module(fp_typing, header=HEADER, extra_aliases=EXTRA_ALIASES)
    # Write the pre-generated modules
    for fp, contents in files.items():
        print(f"Writing\n {schemafile!s}\n  ->{fp!s}")
        ruff_write_lint_format_str(fp, contents)


def _create_encode_signature(
    channel_infos: dict[str, ChannelInfo],
) -> str:
    signature_args: list[str] = ["self", "*args: Any"]
    docstring_parameters: list[str] = ["", "Parameters", "----------"]
    for channel, info in channel_infos.items():
        field_class_name = info.field_class_name
        assert (
            field_class_name is not None
        ), "All channels are expected to have a field class"
        datum_and_value_class_names = []
        if info.datum_class_name is not None:
            datum_and_value_class_names.append(info.datum_class_name)

        if info.value_class_name is not None:
            datum_and_value_class_names.append(info.value_class_name)

        # dict stands for the return types of alt.datum, alt.value as well as
        # the dictionary representation of an encoding channel class. See
        # discussions in https://github.com/vega/altair/pull/3208
        # for more background.
        union_types = ["str", field_class_name, "Map"]
        docstring_union_types = ["str", rst_syntax_for_class(field_class_name), "Dict"]
        if info.supports_arrays:
            # We could be more specific about what types are accepted in the list
            # but then the signatures would get rather long and less useful
            # to a user when it shows up in their IDE.
            union_types.append("list")
            docstring_union_types.append("List")

        union_types = union_types + datum_and_value_class_names
        docstring_union_types = docstring_union_types + [
            rst_syntax_for_class(c) for c in datum_and_value_class_names
        ]

        signature_args.append(
            f"{channel}: Optional[Union[{', '.join(union_types)}]] = Undefined"
        )

        docstring_parameters.extend(
            (
                f"{channel} : {', '.join(docstring_union_types)}",
                f"    {process_description(info.deep_description)}",
            )
        )
    if len(docstring_parameters) > 1:
        docstring_parameters += [""]
    docstring = indent_docstring(
        docstring_parameters, indent_level=4, width=100, lstrip=False
    )
    return ENCODE_METHOD.format(
        encode_method_args=", ".join(signature_args), docstring=docstring
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="generate_schema_wrapper.py", description="Generate the Altair package."
    )
    parser.add_argument(
        "--skip-download", action="store_true", help="skip downloading schema files"
    )
    args = parser.parse_args()
    copy_schemapi_util()
    vegalite_main(args.skip_download)

    # The modules below are imported after the generation of the new schema files
    # as these modules import Altair. This allows them to use the new changes
    from tools import generate_api_docs, update_init_file

    generate_api_docs.write_api_file()
    update_init_file.update__all__variable()


if __name__ == "__main__":
    main()
