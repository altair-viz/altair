import collections
import contextlib
import inspect
import json
import textwrap
from typing import (
    Any,
    Sequence,
    List,
    Dict,
    Optional,
    DefaultDict,
    Tuple,
    Iterable,
    Type,
)
from itertools import zip_longest

import jsonschema
import jsonschema.exceptions
import jsonschema.validators
import numpy as np
import pandas as pd

from altair import vegalite

ValidationErrorList = List[jsonschema.exceptions.ValidationError]
GroupedValidationErrors = Dict[str, ValidationErrorList]


# If DEBUG_MODE is True, then schema objects are converted to dict and
# validated at creation time. This slows things down, particularly for
# larger specs, but leads to much more useful tracebacks for the user.
# Individual schema classes can override this by setting the
# class-level _class_is_valid_at_instantiation attribute to False
DEBUG_MODE = True


def enable_debug_mode():
    global DEBUG_MODE
    DEBUG_MODE = True


def disable_debug_mode():
    global DEBUG_MODE
    DEBUG_MODE = False


@contextlib.contextmanager
def debug_mode(arg):
    global DEBUG_MODE
    original = DEBUG_MODE
    DEBUG_MODE = arg
    try:
        yield
    finally:
        DEBUG_MODE = original


def validate_jsonschema(
    spec: Dict[str, Any],
    schema: Dict[str, Any],
    rootschema: Optional[Dict[str, Any]] = None,
    raise_error: bool = True,
) -> Optional[jsonschema.exceptions.ValidationError]:
    """Validates the passed in spec against the schema in the context of the
    rootschema. If any errors are found, they are deduplicated and prioritized
    and only the most relevant errors are kept. Errors are then either raised
    or returned, depending on the value of `raise_error`.
    """
    errors = _get_errors_from_spec(spec, schema, rootschema=rootschema)
    if errors:
        leaf_errors = _get_leaves_of_error_tree(errors)
        grouped_errors = _group_errors_by_json_path(leaf_errors)
        grouped_errors = _subset_to_most_specific_json_paths(grouped_errors)
        grouped_errors = _deduplicate_errors(grouped_errors)

        # Nothing special about this first error but we need to choose one
        # which can be raised
        main_error = list(grouped_errors.values())[0][0]
        # All errors are then attached as a new attribute to ValidationError so that
        # they can be used in SchemaValidationError to craft a more helpful
        # error message. Setting a new attribute like this is not ideal as
        # it then no longer matches the type ValidationError. It would be better
        # to refactor this function to never raise but only return errors.
        main_error._all_errors = grouped_errors  # type: ignore[attr-defined]
        if raise_error:
            raise main_error
        else:
            return main_error
    else:
        return None


def _get_errors_from_spec(
    spec: Dict[str, Any],
    schema: Dict[str, Any],
    rootschema: Optional[Dict[str, Any]] = None,
) -> ValidationErrorList:
    """Uses the relevant jsonschema validator to validate the passed in spec
    against the schema using the rootschema to resolve references.
    The schema and rootschema themselves are not validated but instead considered
    as validate.
    """
    # We don't use jsonschema.validate as this would validate the schema itself.
    # Instead, we pass the schema directly to the validator class. This is done for
    # two reasons: The schema comes from Vega-Lite and is not based on the user
    # input, therefore there is no need to validate it in the first place. Furthermore,
    # the "uri-reference" format checker fails for some of the references as URIs in
    # "$ref" are not encoded,
    # e.g. '#/definitions/ValueDefWithCondition<MarkPropFieldOrDatumDef,
    # (Gradient|string|null)>' would be a valid $ref in a Vega-Lite schema but
    # it is not a valid URI reference due to the characters such as '<'.
    if rootschema is not None:
        validator_cls = jsonschema.validators.validator_for(rootschema)
        resolver = jsonschema.RefResolver.from_schema(rootschema)
    else:
        validator_cls = jsonschema.validators.validator_for(schema)
        # No resolver is necessary if the schema is already the full schema
        resolver = None

    validator_kwargs = {"resolver": resolver}
    if hasattr(validator_cls, "FORMAT_CHECKER"):
        validator_kwargs["format_checker"] = validator_cls.FORMAT_CHECKER
    validator = validator_cls(schema, **validator_kwargs)
    errors = list(validator.iter_errors(spec))
    return errors


def _group_errors_by_json_path(
    errors: ValidationErrorList,
) -> GroupedValidationErrors:
    """Groups errors by the `json_path` attribute of the jsonschema ValidationError
    class. This attribute contains the path to the offending element within
    a chart specification and can therefore be considered as an identifier of an
    'issue' in the chart that needs to be fixed.
    """
    errors_by_json_path = collections.defaultdict(list)
    for err in errors:
        errors_by_json_path[err.json_path].append(err)
    return dict(errors_by_json_path)


def _get_leaves_of_error_tree(
    errors: ValidationErrorList,
) -> ValidationErrorList:
    """For each error in `errors`, it traverses down the "error tree" that is generated
    by the jsonschema library to find and return all "leaf" errors. These are errors
    which have no further errors that caused it and so they are the most specific errors
    with the most specific error messages.
    """
    leaves: ValidationErrorList = []
    for err in errors:
        if err.context:
            # This means that the error `err` was caused by errors in subschemas.
            # The list of errors from the subschemas are available in the property
            # `context`.
            leaves.extend(_get_leaves_of_error_tree(err.context))
        else:
            leaves.append(err)
    return leaves


def _subset_to_most_specific_json_paths(
    errors_by_json_path: GroupedValidationErrors,
) -> GroupedValidationErrors:
    """Removes key (json path), value (errors) pairs where the json path is fully
    contained in another json path. For example if `errors_by_json_path` has two
    keys, `$.encoding.X` and `$.encoding.X.tooltip`, then the first one will be removed
    and only the second one is returned. This is done under the assumption that
    more specific json paths give more helpful error messages to the user.
    """
    errors_by_json_path_specific: GroupedValidationErrors = {}
    for json_path, errors in errors_by_json_path.items():
        if not _contained_at_start_of_one_of_other_values(
            json_path, list(errors_by_json_path.keys())
        ):
            errors_by_json_path_specific[json_path] = errors
    return errors_by_json_path_specific


def _contained_at_start_of_one_of_other_values(x: str, values: Sequence[str]) -> bool:
    # Does not count as "contained at start of other value" if the values are
    # the same. These cases should be handled separately
    return any(value.startswith(x) for value in values if x != value)


def _deduplicate_errors(
    grouped_errors: GroupedValidationErrors,
) -> GroupedValidationErrors:
    """Some errors have very similar error messages or are just in general not helpful
    for a user. This function removes as many of these cases as possible and
    can be extended over time to handle new cases that come up.
    """
    grouped_errors_deduplicated: GroupedValidationErrors = {}
    for json_path, element_errors in grouped_errors.items():
        errors_by_validator = _group_errors_by_validator(element_errors)

        deduplication_functions = {
            "enum": _deduplicate_enum_errors,
            "additionalProperties": _deduplicate_additional_properties_errors,
        }
        deduplicated_errors: ValidationErrorList = []
        for validator, errors in errors_by_validator.items():
            deduplication_func = deduplication_functions.get(validator, None)
            if deduplication_func is not None:
                errors = deduplication_func(errors)
            deduplicated_errors.extend(_deduplicate_by_message(errors))

        # Removes any ValidationError "'value' is a required property" as these
        # errors are unlikely to be the relevant ones for the user. They come from
        # validation against a schema definition where the output of `alt.value`
        # would be valid. However, if a user uses `alt.value`, the `value` keyword
        # is included automatically from that function and so it's unlikely
        # that this was what the user intended if the keyword is not present
        # in the first place.
        deduplicated_errors = [
            err for err in deduplicated_errors if not _is_required_value_error(err)
        ]

        grouped_errors_deduplicated[json_path] = deduplicated_errors
    return grouped_errors_deduplicated


def _is_required_value_error(err: jsonschema.exceptions.ValidationError) -> bool:
    return err.validator == "required" and err.validator_value == ["value"]


def _group_errors_by_validator(errors: ValidationErrorList) -> GroupedValidationErrors:
    """Groups the errors by the json schema "validator" that casued the error. For
    example if the error is that a value is not one of an enumeration in the json schema
    then the "validator" is `"enum"`, if the error is due to an unknown property that
    was set although no additional properties are allowed then "validator" is
    `"additionalProperties`, etc.
    """
    errors_by_validator: DefaultDict[
        str, ValidationErrorList
    ] = collections.defaultdict(list)
    for err in errors:
        # Ignore mypy error as err.validator as it wrongly sees err.validator
        # as of type Optional[Validator] instead of str
        errors_by_validator[err.validator].append(err)  # type: ignore[index]
    return dict(errors_by_validator)


def _deduplicate_enum_errors(errors: ValidationErrorList) -> ValidationErrorList:
    """Deduplicate enum errors by removing the errors where the allowed values
    are a subset of another error. For example, if `enum` contains two errors
    and one has `validator_value` (i.e. accepted values) ["A", "B"] and the
    other one ["A", "B", "C"] then the first one is removed and the final
    `enum` list only contains the error with ["A", "B", "C"].
    """
    if len(errors) > 1:
        # Values (and therefore `validator_value`) of an enum are always arrays,
        # see https://json-schema.org/understanding-json-schema/reference/generic.html#enumerated-values
        # which is why we can use join below
        value_strings = [",".join(err.validator_value) for err in errors]
        longest_enums: ValidationErrorList = []
        for value_str, err in zip(value_strings, errors):
            if not _contained_at_start_of_one_of_other_values(value_str, value_strings):
                longest_enums.append(err)
        errors = longest_enums
    return errors


def _deduplicate_additional_properties_errors(
    errors: ValidationErrorList,
) -> ValidationErrorList:
    """If there are multiple additional property errors it usually means that
    the offending element was validated against multiple schemas and
    its parent is a common anyOf validator.
    The error messages produced from these cases are usually
    very similar and we just take the shortest one. For example,
    the following 3 errors are raised for the `unknown` channel option in
    `alt.X("variety", unknown=2)`:
    - "Additional properties are not allowed ('unknown' was unexpected)"
    - "Additional properties are not allowed ('field', 'unknown' were unexpected)"
    - "Additional properties are not allowed ('field', 'type', 'unknown' were unexpected)"
    """
    if len(errors) > 1:
        # The code below subsets this to only the first error of the three.
        parent = errors[0].parent
        # Test if all parent errors are the same anyOf error and only do
        # the prioritization in these cases. Can't think of a chart spec where this
        # would not be the case but still allow for it below to not break anything.
        if (
            parent is not None
            and parent.validator == "anyOf"
            and all(err.parent is parent for err in errors[1:])
        ):
            errors = [min(errors, key=lambda x: len(x.message))]
    return errors


def _deduplicate_by_message(errors: ValidationErrorList) -> ValidationErrorList:
    """Deduplicate errors by message. This keeps the original order in case
    it was chosen intentionally.
    """
    return list({e.message: e for e in errors}.values())


def _subclasses(cls):
    """Breadth-first sequence of all classes which inherit from cls."""
    seen = set()
    current_set = {cls}
    while current_set:
        seen |= current_set
        current_set = set.union(*(set(cls.__subclasses__()) for cls in current_set))
        for cls in current_set - seen:
            yield cls


def _todict(obj, context):
    """Convert an object to a dict representation."""
    if isinstance(obj, SchemaBase):
        return obj.to_dict(validate=False, context=context)
    elif isinstance(obj, (list, tuple, np.ndarray)):
        return [_todict(v, context) for v in obj]
    elif isinstance(obj, dict):
        return {k: _todict(v, context) for k, v in obj.items() if v is not Undefined}
    elif hasattr(obj, "to_dict"):
        return obj.to_dict()
    elif isinstance(obj, np.number):
        return float(obj)
    elif isinstance(obj, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(obj).isoformat()
    else:
        return obj


def _resolve_references(schema, root=None):
    """Resolve schema references."""
    resolver = jsonschema.RefResolver.from_schema(root or schema)
    while "$ref" in schema:
        with resolver.resolving(schema["$ref"]) as resolved:
            schema = resolved
    return schema


class SchemaValidationError(jsonschema.ValidationError):
    """A wrapper for jsonschema.ValidationError with friendlier traceback"""

    def __init__(self, obj: "SchemaBase", err: jsonschema.ValidationError) -> None:
        super().__init__(**err._contents())
        self.obj = obj
        self._errors: GroupedValidationErrors = getattr(
            err, "_all_errors", {err.json_path: [err]}
        )
        # This is the message from err
        self._original_message = self.message
        self.message = self._get_message()

    def __str__(self) -> str:
        return self.message

    def _get_message(self) -> str:
        def indent_second_line_onwards(message: str, indent: int = 4) -> str:
            modified_lines: List[str] = []
            for idx, line in enumerate(message.split("\n")):
                if idx > 0 and len(line) > 0:
                    line = " " * indent + line
                modified_lines.append(line)
            return "\n".join(modified_lines)

        error_messages: List[str] = []
        # Only show a maximum of 3 errors as else the messages could get very long.
        for errors in list(self._errors.values())[:3]:
            error_messages.append(self._get_message_for_errors_group(errors))

        message = ""
        if len(error_messages) > 1:
            error_messages = [
                indent_second_line_onwards(f"Error {error_id}: {m}")
                for error_id, m in enumerate(error_messages, start=1)
            ]
            message += "Multiple errors were found.\n\n"
        message += "\n\n".join(error_messages)
        return message

    def _get_message_for_errors_group(
        self,
        errors: ValidationErrorList,
    ) -> str:
        if errors[0].validator == "additionalProperties":
            # During development, we only found cases where an additionalProperties
            # error was raised if that was the only error for the offending instance
            # as identifiable by the json path. Therefore, we just check here the first
            # error. However, other constellations might exist in which case
            # this should be adapted so that other error messages are shown as well.
            message = self._get_additional_properties_error_message(errors[0])
        else:
            message = self._get_default_error_message(errors=errors)

        return message.strip()

    def _get_additional_properties_error_message(
        self,
        error: jsonschema.exceptions.ValidationError,
    ) -> str:
        """Output all existing parameters when an unknown parameter is specified."""
        altair_cls = self._get_altair_class_for_error(error)
        param_dict_keys = inspect.signature(altair_cls).parameters.keys()
        param_names_table = self._format_params_as_table(param_dict_keys)

        # Error messages for these errors look like this:
        # "Additional properties are not allowed ('unknown' was unexpected)"
        # Line below extracts "unknown" from this string
        parameter_name = error.message.split("('")[-1].split("'")[0]
        message = f"""\
`{altair_cls.__name__}` has no parameter named '{parameter_name}'

Existing parameter names are:
{param_names_table}
See the help for `{altair_cls.__name__}` to read the full description of these parameters"""
        return message

    def _get_altair_class_for_error(
        self, error: jsonschema.exceptions.ValidationError
    ) -> Type["SchemaBase"]:
        """Try to get the lowest class possible in the chart hierarchy so
        it can be displayed in the error message. This should lead to more informative
        error messages pointing the user closer to the source of the issue.
        """
        for prop_name in reversed(error.absolute_path):
            # Check if str as e.g. first item can be a 0
            if isinstance(prop_name, str):
                potential_class_name = prop_name[0].upper() + prop_name[1:]
                cls = getattr(vegalite, potential_class_name, None)
                if cls is not None:
                    break
        else:
            # Did not find a suitable class based on traversing the path so we fall
            # back on the class of the top-level object which created
            # the SchemaValidationError
            cls = self.obj.__class__
        return cls

    @staticmethod
    def _format_params_as_table(param_dict_keys: Iterable[str]) -> str:
        """Format param names into a table so that they are easier to read"""
        param_names: Tuple[str, ...]
        name_lengths: Tuple[int, ...]
        param_names, name_lengths = zip(  # type: ignore[assignment]  # Mypy does think it's Tuple[Any]
            *[
                (name, len(name))
                for name in param_dict_keys
                if name not in ["kwds", "self"]
            ]
        )
        # Worst case scenario with the same longest param name in the same
        # row for all columns
        max_name_length = max(name_lengths)
        max_column_width = 80
        # Output a square table if not too big (since it is easier to read)
        num_param_names = len(param_names)
        square_columns = int(np.ceil(num_param_names**0.5))
        columns = min(max_column_width // max_name_length, square_columns)

        # Compute roughly equal column heights to evenly divide the param names
        def split_into_equal_parts(n: int, p: int) -> List[int]:
            return [n // p + 1] * (n % p) + [n // p] * (p - n % p)

        column_heights = split_into_equal_parts(num_param_names, columns)

        # Section the param names into columns and compute their widths
        param_names_columns: List[Tuple[str, ...]] = []
        column_max_widths: List[int] = []
        last_end_idx: int = 0
        for ch in column_heights:
            param_names_columns.append(param_names[last_end_idx : last_end_idx + ch])
            column_max_widths.append(
                max([len(param_name) for param_name in param_names_columns[-1]])
            )
            last_end_idx = ch + last_end_idx

        # Transpose the param name columns into rows to facilitate looping
        param_names_rows: List[Tuple[str, ...]] = []
        for li in zip_longest(*param_names_columns, fillvalue=""):
            param_names_rows.append(li)
        # Build the table as a string by iterating over and formatting the rows
        param_names_table: str = ""
        for param_names_row in param_names_rows:
            for num, param_name in enumerate(param_names_row):
                # Set column width based on the longest param in the column
                max_name_length_column = column_max_widths[num]
                column_pad = 3
                param_names_table += "{:<{}}".format(
                    param_name, max_name_length_column + column_pad
                )
                # Insert newlines and spacing after the last element in each row
                if num == (len(param_names_row) - 1):
                    param_names_table += "\n"
        return param_names_table

    def _get_default_error_message(
        self,
        errors: ValidationErrorList,
    ) -> str:
        bullet_points: List[str] = []
        errors_by_validator = _group_errors_by_validator(errors)
        if "enum" in errors_by_validator:
            for error in errors_by_validator["enum"]:
                bullet_points.append(f"one of {error.validator_value}")

        if "type" in errors_by_validator:
            types = [f"'{err.validator_value}'" for err in errors_by_validator["type"]]
            point = "of type "
            if len(types) == 1:
                point += types[0]
            elif len(types) == 2:
                point += f"{types[0]} or {types[1]}"
            else:
                point += ", ".join(types[:-1]) + f", or {types[-1]}"
            bullet_points.append(point)

        # It should not matter which error is specifically used as they are all
        # about the same offending instance (i.e. invalid value), so we can just
        # take the first one
        error = errors[0]
        # Add a summary line when parameters are passed an invalid value
        # For example: "'asdf' is an invalid value for `stack`
        message = f"'{error.instance}' is an invalid value"
        if error.absolute_path:
            message += f" for `{error.absolute_path[-1]}`"

        # Add bullet points
        if len(bullet_points) == 0:
            message += ".\n\n"
        elif len(bullet_points) == 1:
            message += f". Valid values are {bullet_points[0]}.\n\n"
        else:
            message += ". Valid values are:\n\n"
            message += "\n".join([f"- {point}" for point in bullet_points])
            message += "\n\n"

        # Add unformatted messages of any remaining errors which were not
        # considered so far. This is not expected to be used but more exists
        # as a fallback for cases which were not known during development.
        for validator, errors in errors_by_validator.items():
            if validator not in ("enum", "type"):
                message += "\n".join([e.message for e in errors])

        return message


class UndefinedType:
    """A singleton object for marking undefined parameters"""

    __instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls.__instance, cls):
            cls.__instance = object.__new__(cls, *args, **kwargs)
        return cls.__instance

    def __repr__(self):
        return "Undefined"


# In the future Altair may implement a more complete set of type hints.
# But for now, we'll add an annotation to indicate that the type checker
# should permit any value passed to a function argument whose default
# value is Undefined.
Undefined: Any = UndefinedType()


class SchemaBase:
    """Base class for schema wrappers.

    Each derived class should set the _schema class attribute (and optionally
    the _rootschema class attribute) which is used for validation.
    """

    _schema: Optional[Dict[str, Any]] = None
    _rootschema: Optional[Dict[str, Any]] = None
    _class_is_valid_at_instantiation = True

    def __init__(self, *args, **kwds):
        # Two valid options for initialization, which should be handled by
        # derived classes:
        # - a single arg with no kwds, for, e.g. {'type': 'string'}
        # - zero args with zero or more kwds for {'type': 'object'}
        if self._schema is None:
            raise ValueError(
                "Cannot instantiate object of type {}: "
                "_schema class attribute is not defined."
                "".format(self.__class__)
            )

        if kwds:
            assert len(args) == 0
        else:
            assert len(args) in [0, 1]

        # use object.__setattr__ because we override setattr below.
        object.__setattr__(self, "_args", args)
        object.__setattr__(self, "_kwds", kwds)

        if DEBUG_MODE and self._class_is_valid_at_instantiation:
            self.to_dict(validate=True)

    def copy(self, deep=True, ignore=()):
        """Return a copy of the object

        Parameters
        ----------
        deep : boolean or list, optional
            If True (default) then return a deep copy of all dict, list, and
            SchemaBase objects within the object structure.
            If False, then only copy the top object.
            If a list or iterable, then only copy the listed attributes.
        ignore : list, optional
            A list of keys for which the contents should not be copied, but
            only stored by reference.
        """

        def _shallow_copy(obj):
            if isinstance(obj, SchemaBase):
                return obj.copy(deep=False)
            elif isinstance(obj, list):
                return obj[:]
            elif isinstance(obj, dict):
                return obj.copy()
            else:
                return obj

        def _deep_copy(obj, ignore=()):
            if isinstance(obj, SchemaBase):
                args = tuple(_deep_copy(arg) for arg in obj._args)
                kwds = {
                    k: (_deep_copy(v, ignore=ignore) if k not in ignore else v)
                    for k, v in obj._kwds.items()
                }
                with debug_mode(False):
                    return obj.__class__(*args, **kwds)
            elif isinstance(obj, list):
                return [_deep_copy(v, ignore=ignore) for v in obj]
            elif isinstance(obj, dict):
                return {
                    k: (_deep_copy(v, ignore=ignore) if k not in ignore else v)
                    for k, v in obj.items()
                }
            else:
                return obj

        try:
            deep = list(deep)
        except TypeError:
            deep_is_list = False
        else:
            deep_is_list = True

        if deep and not deep_is_list:
            return _deep_copy(self, ignore=ignore)

        with debug_mode(False):
            copy = self.__class__(*self._args, **self._kwds)
        if deep_is_list:
            for attr in deep:
                copy[attr] = _shallow_copy(copy._get(attr))
        return copy

    def _get(self, attr, default=Undefined):
        """Get an attribute, returning default if not present."""
        attr = self._kwds.get(attr, Undefined)
        if attr is Undefined:
            attr = default
        return attr

    def __getattr__(self, attr):
        # reminder: getattr is called after the normal lookups
        if attr == "_kwds":
            raise AttributeError()
        if attr in self._kwds:
            return self._kwds[attr]
        else:
            try:
                _getattr = super(SchemaBase, self).__getattr__
            except AttributeError:
                _getattr = super(SchemaBase, self).__getattribute__
            return _getattr(attr)

    def __setattr__(self, item, val):
        self._kwds[item] = val

    def __getitem__(self, item):
        return self._kwds[item]

    def __setitem__(self, item, val):
        self._kwds[item] = val

    def __repr__(self):
        if self._kwds:
            args = (
                "{}: {!r}".format(key, val)
                for key, val in sorted(self._kwds.items())
                if val is not Undefined
            )
            args = "\n" + ",\n".join(args)
            return "{0}({{{1}\n}})".format(
                self.__class__.__name__, args.replace("\n", "\n  ")
            )
        else:
            return "{}({!r})".format(self.__class__.__name__, self._args[0])

    def __eq__(self, other):
        return (
            type(self) is type(other)
            and self._args == other._args
            and self._kwds == other._kwds
        )

    def to_dict(self, validate=True, ignore=None, context=None):
        """Return a dictionary representation of the object

        Parameters
        ----------
        validate : boolean
            If True (default), then validate the output dictionary
            against the schema.
        ignore : list
            A list of keys to ignore. This will *not* passed to child to_dict
            function calls.
        context : dict (optional)
            A context dictionary that will be passed to all child to_dict
            function calls

        Returns
        -------
        dct : dictionary
            The dictionary representation of this object

        Raises
        ------
        jsonschema.ValidationError :
            if validate=True and the dict does not conform to the schema
        """
        if context is None:
            context = {}
        if ignore is None:
            ignore = []

        if self._args and not self._kwds:
            result = _todict(self._args[0], context=context)
        elif not self._args:
            kwds = self._kwds.copy()
            # parsed_shorthand is added by FieldChannelMixin.
            # It's used below to replace shorthand with its long form equivalent
            # parsed_shorthand is removed from context if it exists so that it is
            # not passed to child to_dict function calls
            parsed_shorthand = context.pop("parsed_shorthand", {})
            # Prevent that pandas categorical data is automatically sorted
            # when a non-ordinal data type is specifed manually
            # or if the encoding channel does not support sorting
            if "sort" in parsed_shorthand and (
                "sort" not in kwds or kwds["type"] not in ["ordinal", Undefined]
            ):
                parsed_shorthand.pop("sort")

            kwds.update(
                {
                    k: v
                    for k, v in parsed_shorthand.items()
                    if kwds.get(k, Undefined) is Undefined
                }
            )
            kwds = {
                k: v for k, v in kwds.items() if k not in list(ignore) + ["shorthand"]
            }
            if "mark" in kwds and isinstance(kwds["mark"], str):
                kwds["mark"] = {"type": kwds["mark"]}
            result = _todict(
                kwds,
                context=context,
            )
        else:
            raise ValueError(
                "{} instance has both a value and properties : "
                "cannot serialize to dict".format(self.__class__)
            )
        if validate:
            try:
                self.validate(result)
            except jsonschema.ValidationError as err:
                # We do not raise `from err` as else the resulting
                # traceback is very long as it contains part
                # of the Vega-Lite schema. It would also first
                # show the less helpful ValidationError instead of
                # the more user friendly SchemaValidationError
                raise SchemaValidationError(self, err) from None
        return result

    def to_json(
        self,
        validate=True,
        ignore=None,
        context=None,
        indent=2,
        sort_keys=True,
        **kwargs,
    ):
        """Emit the JSON representation for this object as a string.

        Parameters
        ----------
        validate : boolean
            If True (default), then validate the output dictionary
            against the schema.
        ignore : list (optional)
            A list of keys to ignore. This will *not* passed to child to_dict
            function calls.
        context : dict (optional)
            A context dictionary that will be passed to all child to_dict
            function calls
        indent : integer, default 2
            the number of spaces of indentation to use
        sort_keys : boolean, default True
            if True, sort keys in the output
        **kwargs
            Additional keyword arguments are passed to ``json.dumps()``

        Returns
        -------
        spec : string
            The JSON specification of the chart object.
        """
        if ignore is None:
            ignore = []
        if context is None:
            context = {}
        dct = self.to_dict(validate=validate, ignore=ignore, context=context)
        return json.dumps(dct, indent=indent, sort_keys=sort_keys, **kwargs)

    @classmethod
    def _default_wrapper_classes(cls):
        """Return the set of classes used within cls.from_dict()"""
        return _subclasses(SchemaBase)

    @classmethod
    def from_dict(cls, dct, validate=True, _wrapper_classes=None):
        """Construct class from a dictionary representation

        Parameters
        ----------
        dct : dictionary
            The dict from which to construct the class
        validate : boolean
            If True (default), then validate the input against the schema.
        _wrapper_classes : list (optional)
            The set of SchemaBase classes to use when constructing wrappers
            of the dict inputs. If not specified, the result of
            cls._default_wrapper_classes will be used.

        Returns
        -------
        obj : Schema object
            The wrapped schema

        Raises
        ------
        jsonschema.ValidationError :
            if validate=True and dct does not conform to the schema
        """
        if validate:
            cls.validate(dct)
        if _wrapper_classes is None:
            _wrapper_classes = cls._default_wrapper_classes()
        converter = _FromDict(_wrapper_classes)
        return converter.from_dict(dct, cls)

    @classmethod
    def from_json(cls, json_string, validate=True, **kwargs):
        """Instantiate the object from a valid JSON string

        Parameters
        ----------
        json_string : string
            The string containing a valid JSON chart specification.
        validate : boolean
            If True (default), then validate the input against the schema.
        **kwargs :
            Additional keyword arguments are passed to json.loads

        Returns
        -------
        chart : Chart object
            The altair Chart object built from the specification.
        """
        dct = json.loads(json_string, **kwargs)
        return cls.from_dict(dct, validate=validate)

    @classmethod
    def validate(cls, instance, schema=None):
        """
        Validate the instance against the class schema in the context of the
        rootschema.
        """
        if schema is None:
            schema = cls._schema
        return validate_jsonschema(
            instance, schema, rootschema=cls._rootschema or cls._schema
        )

    @classmethod
    def resolve_references(cls, schema=None):
        """Resolve references in the context of this object's schema or root schema."""
        return _resolve_references(
            schema=(schema or cls._schema),
            root=(cls._rootschema or cls._schema or schema),
        )

    @classmethod
    def validate_property(cls, name, value, schema=None):
        """
        Validate a property against property schema in the context of the
        rootschema
        """
        value = _todict(value, context={})
        props = cls.resolve_references(schema or cls._schema).get("properties", {})
        return validate_jsonschema(
            value, props.get(name, {}), rootschema=cls._rootschema or cls._schema
        )

    def __dir__(self):
        return sorted(super().__dir__() + list(self._kwds.keys()))


def _passthrough(*args, **kwds):
    return args[0] if args else kwds


class _FromDict:
    """Class used to construct SchemaBase class hierarchies from a dict

    The primary purpose of using this class is to be able to build a hash table
    that maps schemas to their wrapper classes. The candidate classes are
    specified in the ``class_list`` argument to the constructor.
    """

    _hash_exclude_keys = ("definitions", "title", "description", "$schema", "id")

    def __init__(self, class_list):
        # Create a mapping of a schema hash to a list of matching classes
        # This lets us quickly determine the correct class to construct
        self.class_dict = collections.defaultdict(list)
        for cls in class_list:
            if cls._schema is not None:
                self.class_dict[self.hash_schema(cls._schema)].append(cls)

    @classmethod
    def hash_schema(cls, schema, use_json=True):
        """
        Compute a python hash for a nested dictionary which
        properly handles dicts, lists, sets, and tuples.

        At the top level, the function excludes from the hashed schema all keys
        listed in `exclude_keys`.

        This implements two methods: one based on conversion to JSON, and one based
        on recursive conversions of unhashable to hashable types; the former seems
        to be slightly faster in several benchmarks.
        """
        if cls._hash_exclude_keys and isinstance(schema, dict):
            schema = {
                key: val
                for key, val in schema.items()
                if key not in cls._hash_exclude_keys
            }
        if use_json:
            s = json.dumps(schema, sort_keys=True)
            return hash(s)
        else:

            def _freeze(val):
                if isinstance(val, dict):
                    return frozenset((k, _freeze(v)) for k, v in val.items())
                elif isinstance(val, set):
                    return frozenset(map(_freeze, val))
                elif isinstance(val, list) or isinstance(val, tuple):
                    return tuple(map(_freeze, val))
                else:
                    return val

            return hash(_freeze(schema))

    def from_dict(
        self, dct, cls=None, schema=None, rootschema=None, default_class=_passthrough
    ):
        """Construct an object from a dict representation"""
        if (schema is None) == (cls is None):
            raise ValueError("Must provide either cls or schema, but not both.")
        if schema is None:
            schema = schema or cls._schema
            rootschema = rootschema or cls._rootschema
        rootschema = rootschema or schema

        if isinstance(dct, SchemaBase):
            return dct

        if cls is None:
            # If there are multiple matches, we use the first one in the dict.
            # Our class dict is constructed breadth-first from top to bottom,
            # so the first class that matches is the most general match.
            matches = self.class_dict[self.hash_schema(schema)]
            if matches:
                cls = matches[0]
            else:
                cls = default_class
        schema = _resolve_references(schema, rootschema)

        if "anyOf" in schema or "oneOf" in schema:
            schemas = schema.get("anyOf", []) + schema.get("oneOf", [])
            for possible_schema in schemas:
                try:
                    validate_jsonschema(dct, possible_schema, rootschema=rootschema)
                except jsonschema.ValidationError:
                    continue
                else:
                    return self.from_dict(
                        dct,
                        schema=possible_schema,
                        rootschema=rootschema,
                        default_class=cls,
                    )

        if isinstance(dct, dict):
            # TODO: handle schemas for additionalProperties/patternProperties
            props = schema.get("properties", {})
            kwds = {}
            for key, val in dct.items():
                if key in props:
                    val = self.from_dict(val, schema=props[key], rootschema=rootschema)
                kwds[key] = val
            return cls(**kwds)

        elif isinstance(dct, list):
            item_schema = schema.get("items", {})
            dct = [
                self.from_dict(val, schema=item_schema, rootschema=rootschema)
                for val in dct
            ]
            return cls(dct)
        else:
            return cls(dct)


class _PropertySetter:
    def __init__(self, prop, schema):
        self.prop = prop
        self.schema = schema

    def __get__(self, obj, cls):
        self.obj = obj
        self.cls = cls
        # The docs from the encoding class parameter (e.g. `bin` in X, Color,
        # etc); this provides a general description of the parameter.
        self.__doc__ = self.schema["description"].replace("__", "**")
        property_name = f"{self.prop}"[0].upper() + f"{self.prop}"[1:]
        if hasattr(vegalite, property_name):
            altair_prop = getattr(vegalite, property_name)
            # Add the docstring from the helper class (e.g. `BinParams`) so
            # that all the parameter names of the helper class are included in
            # the final docstring
            parameter_index = altair_prop.__doc__.find("Parameters\n")
            if parameter_index > -1:
                self.__doc__ = (
                    altair_prop.__doc__[:parameter_index].replace("    ", "")
                    + self.__doc__
                    + textwrap.dedent(
                        f"\n\n    {altair_prop.__doc__[parameter_index:]}"
                    )
                )
            # For short docstrings such as Aggregate, Stack, et
            else:
                self.__doc__ = (
                    altair_prop.__doc__.replace("    ", "") + "\n" + self.__doc__
                )
            # Add signatures and tab completion for the method and parameter names
            self.__signature__ = inspect.signature(altair_prop)
            self.__wrapped__ = inspect.getfullargspec(altair_prop)
            self.__name__ = altair_prop.__name__
        else:
            # It seems like bandPosition is the only parameter that doesn't
            # have a helper class.
            pass
        return self

    def __call__(self, *args, **kwargs):
        obj = self.obj.copy()
        # TODO: use schema to validate
        obj[self.prop] = args[0] if args else kwargs
        return obj


def with_property_setters(cls):
    """
    Decorator to add property setters to a Schema class.
    """
    schema = cls.resolve_references()
    for prop, propschema in schema.get("properties", {}).items():
        setattr(cls, prop, _PropertySetter(prop, propschema))
    return cls
