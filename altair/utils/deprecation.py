from __future__ import annotations

from typing import TypeVar
from inspect import ismethod
import typing_extensions as te


_T = TypeVar("_T")


class AltairDeprecationWarning(DeprecationWarning): ...


class deprecated(te.deprecated):
    """Indicate that a class, function or overload is deprecated.

    When this decorator is applied to an object, the type checker
    will generate a diagnostic on usage of the deprecated object.

    Parameters
    ----------
    message
        Additional message appended to ``version``, ``alternative``.
    version
        ``altair`` version the deprecation first appeared.
    alternative
        Suggested replacement class/method/function.
    category
        If the *category* is ``None``, no warning is emitted at runtime.
    stacklevel
        The *stacklevel* determines where the
        warning is emitted. If it is ``1`` (the default), the warning
        is emitted at the direct caller of the deprecated object; if it
        is higher, it is emitted further up the stack.
        Static type checker behavior is not affected by the *category*
        and *stacklevel* arguments.
    """

    def __init__(
        self,
        message: te.LiteralString,
        /,
        *,
        version: str,
        alternative: str | None = None,
        category: type[AltairDeprecationWarning] | None = AltairDeprecationWarning,
        stacklevel: int = 1,
    ) -> None:
        super().__init__(message, category=category, stacklevel=stacklevel)
        self.version = version
        self.alternative = alternative

    def __call__(self, arg: _T, /) -> _T:
        if name := getattr(arg, "__name__"):  # noqa: B009
            # HACK:
            # - The annotation for `arg` is required for `mypy` to be happy
            # - The attribute check is for `pyright`
            ...
        else:
            msg = (
                f"{type(self).__qualname__!r} can only be used on"
                f" types with a '__name__' attribute, and {arg!r} does not.\n\n"
                "See https://docs.python.org/3/reference/datamodel.html#callable-types"
            )
            raise TypeError(msg)
        msg = f"alt.{name} was deprecated in `altair={self.version}`."
        if self.alternative:
            prefix = arg.__qualname__.split(".")[0] if ismethod(arg) else "alt"
            msg = f"{msg} Use {prefix}.{self.alternative} instead."
        self.message = f"{msg}\n\n{self.message}" if self.message else msg  # pyright: ignore[reportAttributeAccessIssue]
        return super().__call__(arg)


# NOTE: Annotating the return type breaks `pyright` detecting [reportDeprecated]
def deprecate(
    *,
    version: te.LiteralString,
    alternative: te.LiteralString | None = None,
    message: te.LiteralString | None = None,
    category: type[AltairDeprecationWarning] | None = AltairDeprecationWarning,
    stacklevel: int = 1,
):
    """Indicate that a class, function or overload is deprecated.

    When this decorator is applied to an object, the type checker
    will generate a diagnostic on usage of the deprecated object.

    Parameters
    ----------
    version
        ``altair`` version the deprecation first appeared.
    alternative
        Suggested replacement class/method/function.
    message
        Additional message appended to ``version``, ``alternative``.
    category
        If the *category* is ``None``, no warning is emitted at runtime.
    stacklevel
        The *stacklevel* determines where the
        warning is emitted. If it is ``1`` (the default), the warning
        is emitted at the direct caller of the deprecated object; if it
        is higher, it is emitted further up the stack.
        Static type checker behavior is not affected by the *category*
        and *stacklevel* arguments.
    """
    output = f"Deprecated in `altair={version}`."
    if alternative:
        output = f"{output} Use {alternative} instead."
    return te.deprecated(
        f"{output}\n\n{message}" if message else output,
        category=category,
        stacklevel=stacklevel,
    )


def msg(
    *,
    version: te.LiteralString,
    alternative: te.LiteralString | None = None,
    message: te.LiteralString | None = None,
) -> te.LiteralString:
    """Generate a standard deprecation message.

    Parameters
    ----------
    version
        ``altair`` version the deprecation first appeared.
    alternative
        Suggested replacement class/method/function.
    message
        Additional message appended to ``version``, ``alternative``.
    """
    output = f"Deprecated in `altair={version}`."
    if alternative:
        output = f"{output} Use {alternative} instead."
    return f"{output}\n\n{message}" if message else output
