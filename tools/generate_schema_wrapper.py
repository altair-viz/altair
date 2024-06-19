"""Generate a schema wrapper from a schema"""

import argparse
import copy
import json
import os
import re
import sys
import textwrap
from dataclasses import dataclass
from os.path import abspath, dirname, join
from typing import Dict, Final, List, Literal, Optional, Tuple, Type, Union
from urllib import request

import m2r

# Add path so that schemapi can be imported from the tools folder
current_dir = dirname(__file__)
sys.path.insert(0, abspath(current_dir))
# And another path so that Altair can be imported from head. This is relevant when
# generate_api_docs is imported in the main function
sys.path.insert(0, abspath(join(current_dir, "..")))
from schemapi import codegen  # noqa: E402
from schemapi.codegen import CodeSnippet  # noqa: E402
from schemapi.utils import (  # noqa: E402
    SchemaInfo,
    get_valid_identifier,
    resolve_references,
    ruff_format_str,
    rst_syntax_for_class,
    indent_docstring,
)

SCHEMA_VERSION: Final = "v5.17.0"

reLink = re.compile(r"(?<=\[)([^\]]+)(?=\]\([^\)]+\))", re.M)
reSpecial = re.compile(r"[*_]{2,3}|`", re.M)

HEADER: Final = """\
# The contents of this file are automatically written by
# tools/generate_schema_wrapper.py. Do not modify directly.
"""

SCHEMA_URL_TEMPLATE: Final = "https://vega.github.io/schema/" "{library}/{version}.json"

CHANNEL_MYPY_IGNORE_STATEMENTS: Final = """\
# These errors need to be ignored as they come from the overload methods
# which trigger two kind of errors in mypy:
# * all of them do not have an implementation in this file
# * some of them are the only overload methods -> overloads usually only make
#   sense if there are multiple ones
# However, we need these overloads due to how the propertysetter works
# mypy: disable-error-code="no-overload-impl, empty-body, misc"
"""

PARAMETER_PROTOCOL: Final = """
class _Parameter(Protocol):
    # This protocol represents a Parameter as defined in api.py
    # It would be better if we could directly use the Parameter class,
    # but that would create a circular import.
    # The protocol does not need to have all the attributes and methods of this
    # class but the actual api.Parameter just needs to pass a type check
    # as a core._Parameter.

    _counter: int

    def _get_name(cls) -> str:
        ...

    def to_dict(self) -> TypingDict[str, Union[str, dict]]:
        ...

    def _to_expr(self) -> str:
        ...
"""

BASE_SCHEMA: Final = """
class {basename}(SchemaBase):
    _rootschema = load_schema()
    @classmethod
    def _default_wrapper_classes(cls) -> TypingGenerator[type, None, None]:
        return _subclasses({basename})
"""

LOAD_SCHEMA: Final = '''
import pkgutil
import json

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
    def to_dict(
        self,
        validate: bool = True,
        ignore: Optional[List[str]] = None,
        context: Optional[TypingDict[str, Any]] = None,
    ) -> Union[dict, List[dict]]:
        context = context or {}
        ignore = ignore or []
        shorthand = self._get("shorthand")  # type: ignore[attr-defined]
        field = self._get("field")  # type: ignore[attr-defined]

        if shorthand is not Undefined and field is not Undefined:
            raise ValueError(
                "{} specifies both shorthand={} and field={}. "
                "".format(self.__class__.__name__, shorthand, field)
            )

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
                if isinstance(context.get("data", None), DataFrameLike):
                    raise ValueError(
                        'Unable to determine data type for the field "{}";'
                        " verify that the field name is not misspelled."
                        " If you are referencing a field from a transform,"
                        " also confirm that the data type is specified correctly.".format(
                            shorthand
                        )
                    )
                else:
                    raise ValueError(
                        "{} encoding field is specified without a type; "
                        "the type cannot be automatically inferred because "
                        "the data is not specified as a pandas.DataFrame."
                        "".format(shorthand)
                    )
        else:
            # Shorthand is not a string; we pass the definition to field,
            # and do not do any parsing.
            parsed = {"field": shorthand}
        context["parsed_shorthand"] = parsed

        return super(FieldChannelMixin, self).to_dict(
            validate=validate, ignore=ignore, context=context
        )


class ValueChannelMixin:
    def to_dict(
        self,
        validate: bool = True,
        ignore: Optional[List[str]] = None,
        context: Optional[TypingDict[str, Any]] = None,
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
    def to_dict(
        self,
        validate: bool = True,
        ignore: Optional[List[str]] = None,
        context: Optional[TypingDict[str, Any]] = None,
    ) -> dict:
        context = context or {}
        ignore = ignore or []
        datum = self._get("datum", Undefined)  # type: ignore[attr-defined]
        copy = self  # don't copy unless we need to
        if datum is not Undefined:
            if isinstance(datum, core.SchemaBase):
                pass
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

ENCODE_SIGNATURE: Final = '''
def _encode_signature({encode_method_args}):
    """{docstring}"""
    ...
'''


class SchemaGenerator(codegen.SchemaGenerator):
    schema_class_template = textwrap.dedent(
        '''
    class {classname}({basename}):
        """{docstring}"""
        _schema = {schema!r}

        {init_code}
    '''
    )

    def _process_description(self, description: str) -> str:
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
    version: str, schemapath: str, skip_download: bool = False
) -> str:
    url = schema_url(version=version)
    if not os.path.exists(schemapath):
        os.makedirs(schemapath)
    filename = os.path.join(schemapath, "vega-lite-schema.json")
    if not skip_download:
        request.urlretrieve(url, filename)
    elif not os.path.exists(filename):
        raise ValueError("Cannot skip download: {} does not exist".format(filename))
    return filename


def load_schema_with_shorthand_properties(schemapath: str) -> dict:
    with open(schemapath, encoding="utf8") as f:
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
            else:
                if "shorthand" not in defschema["required"]:
                    defschema["required"].append("shorthand")
            schema["definitions"][field_ref.split("/")[-1]] = defschema
    return schema


def copy_schemapi_util() -> None:
    """
    Copy the schemapi utility into altair/utils/ and its test file to tests/utils/
    """
    # copy the schemapi utility file
    source_path = abspath(join(dirname(__file__), "schemapi", "schemapi.py"))
    destination_path = abspath(
        join(dirname(__file__), "..", "altair", "utils", "schemapi.py")
    )

    print("Copying\n {}\n  -> {}".format(source_path, destination_path))
    with open(source_path, "r", encoding="utf8") as source:
        with open(destination_path, "w", encoding="utf8") as dest:
            dest.write(HEADER)
            dest.writelines(source.readlines())


def recursive_dict_update(schema: dict, root: dict, def_dict: dict) -> None:
    if "$ref" in schema:
        next_schema = resolve_references(schema, root)
        if "properties" in next_schema:
            definition = schema["$ref"]
            properties = next_schema["properties"]
            for k in def_dict.keys():
                if k in properties:
                    def_dict[k] = definition
        else:
            recursive_dict_update(next_schema, root, def_dict)
    elif "anyOf" in schema:
        for sub_schema in schema["anyOf"]:
            recursive_dict_update(sub_schema, root, def_dict)


def get_field_datum_value_defs(propschema: SchemaInfo, root: dict) -> dict:
    def_dict: Dict[str, Optional[str]] = {k: None for k in ("field", "datum", "value")}
    schema = propschema.schema
    if propschema.is_reference() and "properties" in schema:
        if "field" in schema["properties"]:
            def_dict["field"] = propschema.ref
        else:
            raise ValueError("Unexpected schema structure")
    else:
        recursive_dict_update(schema, root, def_dict)

    return {i: j for i, j in def_dict.items() if j}


def toposort(graph: Dict[str, List[str]]) -> List[str]:
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
    stack: List[str] = []
    visited: Dict[str, Literal[True]] = {}

    def visit(nodes):
        for node in sorted(nodes, reverse=True):
            if not visited.get(node):
                visited[node] = True
                visit(graph.get(node, []))
                stack.insert(0, node)

    visit(graph)
    return stack


def generate_vegalite_schema_wrapper(schema_file: str) -> str:
    """Generate a schema wrapper at the given path."""
    # TODO: generate simple tests for each wrapper
    basename = "VegaLiteSchema"

    rootschema = load_schema_with_shorthand_properties(schema_file)

    definitions: Dict[str, SchemaGenerator] = {}

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
            rootschemarepr=CodeSnippet("{}._rootschema".format(basename)),
        )

    graph: Dict[str, List[str]] = {}

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
    # of exported classes which are also defined in the channels module which takes
    # precedent in the generated __init__.py file one level up where core.py
    # and channels.py are imported. Importing both confuses type checkers.
    all_ = [
        c for c in definitions if not c.startswith("_") and c not in ("Color", "Text")
    ] + [
        "Root",
        "VegaLiteSchema",
        "SchemaBase",
        "load_schema",
    ]

    contents = [
        HEADER,
        "__all__ = {}".format(all_),
        "from typing import Any, Literal, Union, Protocol, Sequence, List",
        "from typing import Dict as TypingDict",
        "from typing import Generator as TypingGenerator" "",
        "from altair.utils.schemapi import SchemaBase, Undefined, UndefinedType, _subclasses",
        LOAD_SCHEMA.format(schemafile="vega-lite-schema.json"),
    ]
    contents.append(PARAMETER_PROTOCOL)
    contents.append(BASE_SCHEMA.format(basename=basename))
    contents.append(
        schema_class(
            "Root",
            schema=rootschema,
            basename=basename,
            schemarepr=CodeSnippet("{}._rootschema".format(basename)),
        )
    )

    for name in toposort(graph):
        contents.append(definitions[name].schema_class())

    contents.append("")  # end with newline
    return "\n".join(contents)


@dataclass
class ChannelInfo:
    supports_arrays: bool
    deep_description: str
    field_class_name: Optional[str] = None
    datum_class_name: Optional[str] = None
    value_class_name: Optional[str] = None


def generate_vegalite_channel_wrappers(
    schemafile: str, version: str, imports: Optional[List[str]] = None
) -> str:
    # TODO: generate __all__ for top of file
    schema = load_schema_with_shorthand_properties(schemafile)
    if imports is None:
        imports = [
            "import sys",
            "from . import core",
            "from altair.utils.core import DataFrameLike",
            "from altair.utils.schemapi import Undefined, UndefinedType, with_property_setters",
            "from altair.utils import parse_shorthand",
            "from typing import Any, overload, Sequence, List, Literal, Union, Optional",
            "from typing import Dict as TypingDict",
        ]
    contents = [HEADER]
    contents.append(CHANNEL_MYPY_IGNORE_STATEMENTS)
    contents.extend(imports)
    contents.append("")

    contents.append(CHANNEL_MIXINS)

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
            basename = definition.split("/")[-1]
            basename = get_valid_identifier(basename)

            defschema = {"$ref": definition}

            Generator: Union[
                Type[FieldSchemaGenerator],
                Type[DatumSchemaGenerator],
                Type[ValueSchemaGenerator],
            ]
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
    schemafile: str, markdefs: Dict[str, str]
) -> Tuple[List[str], str]:
    with open(schemafile, encoding="utf8") as f:
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
        info = SchemaInfo({"$ref": "#/definitions/" + mark_def}, rootschema=schema)

        # adapted from SchemaInfo.init_code
        arg_info = codegen.get_args(info)
        arg_info.required -= {"type"}
        arg_info.kwds -= {"type"}

        def_args = ["self"] + [
            f"{p}: "
            + info.properties[p].get_python_type_representation(
                for_type_hints=True,
                altair_classes_prefix="core",
                additional_type_hints=["UndefinedType"],
            )
            + " = Undefined"
            for p in (sorted(arg_info.required) + sorted(arg_info.kwds))
        ]
        dict_args = [
            "{0}={0}".format(p)
            for p in (sorted(arg_info.required) + sorted(arg_info.kwds))
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


def generate_vegalite_config_mixin(schemafile: str) -> Tuple[List[str], str]:
    imports = ["from . import core", "from altair.utils import use_signature"]

    class_name = "ConfigMethodMixin"

    code = [
        f"class {class_name}:",
        '    """A mixin class that defines config methods"""',
    ]
    with open(schemafile, encoding="utf8") as f:
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
    path = abspath(
        join(dirname(__file__), "..", "altair", "vegalite", version.split(".")[0])
    )
    schemapath = os.path.join(path, "schema")
    schemafile = download_schemafile(
        version=version,
        schemapath=schemapath,
        skip_download=skip_download,
    )

    # Generate __init__.py file
    outfile = join(schemapath, "__init__.py")
    print("Writing {}".format(outfile))
    content = [
        "# ruff: noqa\n",
        "from .core import *\nfrom .channels import *\n",
        f"SCHEMA_VERSION = '{version}'\n",
        "SCHEMA_URL = {!r}\n" "".format(schema_url(version)),
    ]
    with open(outfile, "w", encoding="utf8") as f:
        f.write(ruff_format_str(content))

    # Generate the core schema wrappers
    outfile = join(schemapath, "core.py")
    print("Generating\n {}\n  ->{}".format(schemafile, outfile))
    file_contents = generate_vegalite_schema_wrapper(schemafile)
    with open(outfile, "w", encoding="utf8") as f:
        f.write(ruff_format_str(file_contents))

    # Generate the channel wrappers
    outfile = join(schemapath, "channels.py")
    print("Generating\n {}\n  ->{}".format(schemafile, outfile))
    code = generate_vegalite_channel_wrappers(schemafile, version=version)
    with open(outfile, "w", encoding="utf8") as f:
        f.write(ruff_format_str(code))

    # generate the mark mixin
    markdefs = {k: k + "Def" for k in ["Mark", "BoxPlot", "ErrorBar", "ErrorBand"]}
    outfile = join(schemapath, "mixins.py")
    print("Generating\n {}\n  ->{}".format(schemafile, outfile))
    mark_imports, mark_mixin = generate_vegalite_mark_mixin(schemafile, markdefs)
    config_imports, config_mixin = generate_vegalite_config_mixin(schemafile)
    try_except_imports = [
        "if sys.version_info >= (3, 11):",
        "    from typing import Self",
        "else:",
        "    from typing_extensions import Self",
    ]
    stdlib_imports = ["import sys"]
    imports = sorted(set(mark_imports + config_imports))
    content = [
        HEADER,
        "\n".join(stdlib_imports),
        "\n\n",
        "\n".join(imports),
        "\n\n",
        "\n".join(try_except_imports),
        "\n\n\n",
        mark_mixin,
        "\n\n\n",
        config_mixin,
    ]
    with open(outfile, "w", encoding="utf8") as f:
        f.write(ruff_format_str(content))


def _create_encode_signature(
    channel_infos: Dict[str, ChannelInfo],
) -> str:
    signature_args: list[str] = ["self"]
    docstring_parameters: list[str] = ["", "Parameters", "----------", ""]
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
        union_types = ["str", field_class_name, "dict"]
        docstring_union_types = ["str", rst_syntax_for_class(field_class_name), "Dict"]
        if info.supports_arrays:
            # We could be more specific about what types are accepted in the list
            # but then the signatures would get rather long and less useful
            # to a user when it shows up in their IDE.
            union_types.append("list")
            docstring_union_types.append("List")

        union_types = union_types + datum_and_value_class_names + ["UndefinedType"]
        docstring_union_types = docstring_union_types + [
            rst_syntax_for_class(c) for c in datum_and_value_class_names
        ]

        signature_args.append(f"{channel}: Union[{', '.join(union_types)}] = Undefined")

        docstring_parameters.append(f"{channel} : {', '.join(docstring_union_types)}")
        docstring_parameters.append(
            "    {}".format(process_description(info.deep_description))
        )
    if len(docstring_parameters) > 1:
        docstring_parameters += [""]
    docstring = indent_docstring(
        docstring_parameters, indent_level=4, width=100, lstrip=True
    )
    return ENCODE_SIGNATURE.format(
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
    import generate_api_docs  # noqa: E402
    import update_init_file  # noqa: E402

    generate_api_docs.write_api_file()
    update_init_file.update__all__variable()


if __name__ == "__main__":
    main()
