"""Path: src/gda/core/introspectable.py

Runtime introspection mixin for self-documenting archive components.

Operational Role:
    Provides class- and instance-level runtime discovery for domain classes.
    Inspects docstrings, signatures, and runtime values, emitting structured
    directory listings and member-specific documentation to stdout or as strings.

Classes:
    _HybridHelpDescriptor: Descriptor binding .help() across classes and instances.
    IntrospectableMixin: Composition mixin furnishing runtime .help() capabilities.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from gda.core.errors import GenealogyDeskError

__version__ = "1.0.0+build.9"

__all__ = [
    "IntrospectableMixin",
]


def _render_property_help(
    cls: type[IntrospectableMixin],
    instance: Any,
    clean_name: str,
    prop_attr: property,
) -> list[str]:
    """Format single-member help lines for a property descriptor."""
    doc = inspect.getdoc(prop_attr.fget) or "No documentation provided."
    if instance is not None:
        try:
            current_val = getattr(instance, clean_name)
        except Exception as err:
            # Capture runtime property evaluation errors gracefully
            current_val = f"<Error evaluating: {err}>"
    else:
        current_val = "<Unbound property: call help() on an instance to inspect value>"

    return [
        f"\nHelp on property '{cls.__name__}.{clean_name}':",
        f"  Current Value: {current_val}",
        f"  Description:   {doc}\n",
    ]


def _render_callable_help(
    cls: type[IntrospectableMixin],
    instance: Any,
    clean_name: str,
    callable_attr: Any,
) -> list[str]:
    """Format single-member help lines for a callable method."""
    doc = inspect.getdoc(callable_attr) or "No documentation provided."
    target_callable = getattr(instance, clean_name) if instance is not None else callable_attr
    try:
        sig_str = str(inspect.signature(target_callable))
    except (ValueError, TypeError):
        # Fallback when C-extensions or built-ins cannot be introspected
        sig_str = "(...)"

    return [
        f"\nHelp on method '{cls.__name__}.{clean_name}':",
        f"  Signature:   {clean_name}{sig_str}",
        f"  Description: {doc}\n",
    ]


def _render_member_help(
    cls: type[IntrospectableMixin],
    instance: Any,
    clean_name: str,
) -> str:
    """Inspect and format documentation for a single named member on cls."""
    cls_attr = getattr(cls, clean_name, None)
    # Guard against requests for non-existent class attributes
    if cls_attr is None:
        raise GenealogyDeskError(
            f"'{clean_name}' is not a recognized member of {cls.__name__}.",
            error_code="ERR_MEMBER_NOT_FOUND",
            details={"class": cls.__name__, "member": clean_name},
        )

    if isinstance(cls_attr, property):
        output_lines = _render_property_help(cls, instance, clean_name, cls_attr)
    elif callable(cls_attr):
        output_lines = _render_callable_help(cls, instance, clean_name, cls_attr)
    else:
        output_lines = [
            f"\nHelp on attribute '{cls.__name__}.{clean_name}':",
            f"  Value: {cls_attr}",
            f"  Type:  {type(cls_attr).__name__}\n",
        ]

    return "\n".join(output_lines)


def _render_directory_help(cls: type[IntrospectableMixin]) -> str:
    """Format the full public directory of properties and callable methods for cls."""
    props, meths = cls._get_public_members()
    lines = [f"\n=== {cls.__name__} Public Directory ==="]

    if props:
        lines.append("\nProperties (Attributes & Paths):")
        for p in props:
            prop_obj = getattr(cls, p, None)
            prop_doc: str | None = (
                inspect.getdoc(prop_obj.fget) if isinstance(prop_obj, property) else None
            )
            first_line = prop_doc.splitlines()[0] if prop_doc else "No description available."
            lines.append(f"  • {p:<25} - {first_line}")

    if meths:
        lines.append("\nCallable Methods:")
        for m in meths:
            meth_obj = getattr(cls, m, None)
            meth_doc: str | None = inspect.getdoc(meth_obj) if callable(meth_obj) else None
            first_line = meth_doc.splitlines()[0] if meth_doc else "No description available."
            lines.append(f"  • {m:<25} - {first_line}")

    lines.append("\nTip: Call .help('name') on your instance or class for full details.\n")
    return "\n".join(lines)


class _HybridHelpDescriptor:
    """Enable .help() to function seamlessly as both a classmethod and an instancemethod."""

    def __get__(
        self,
        instance: Any,
        owner: type[IntrospectableMixin] | None = None,
    ) -> Callable[..., str | None]:
        """Bind the introspection dispatcher to the target class or instance.

        Args:
            instance: Active instance invoking help(), or None if called on the class.
            owner: Class type declaring or inheriting IntrospectableMixin.

        Returns:
            Callable dispatcher executing member inspection or public directory listing.
        """
        cls: type[IntrospectableMixin] = owner if owner is not None else type(instance)

        def help_dispatcher(
            member_name: str | None = None,
            *,
            as_str: bool = False,
        ) -> str | None:
            """Inspect class members or render an indexed public directory.

            Args:
                member_name: Optional name of the specific property or method to inspect.
                as_str: If True, returns the formatted string instead of printing.

            Returns:
                Formatted documentation string if as_str=True; None otherwise.

            Raises:
                GenealogyDeskError: If member_name does not exist on the owner class.
            """
            clean_name = member_name.strip() if member_name else ""
            result = (
                _render_member_help(cls, instance, clean_name)
                if clean_name
                else _render_directory_help(cls)
            )
            if as_str:
                return result
            print(result)
            return None

        return help_dispatcher


class IntrospectableMixin:
    """Provide dual class- and instance-level runtime directory inspection.

    Subclasses inherit the self-documenting .help() method, allowing operators
    to inspect public properties, methods, call signatures, and live values.
    """

    help = _HybridHelpDescriptor()

    @classmethod
    def _get_public_members(cls) -> tuple[list[str], list[str]]:
        """Discover and categorize public properties and callable methods on the class.

        Excludes private/protected names (prefixed with '_') and the 'help'
        descriptor itself.

        Returns:
            Tuple of (sorted property names, sorted callable method names).
        """
        props: set[str] = set()
        meths: set[str] = set()

        # Traverse the MRO to collect public descriptors and callables
        for base in cls.__mro__:
            if base is object:
                continue
            for name, raw_attr in base.__dict__.items():
                if name.startswith("_") or name == "help":
                    continue
                resolved = getattr(cls, name, None)
                if isinstance(raw_attr, property) or isinstance(resolved, property):
                    props.add(name)
                elif callable(resolved) or isinstance(raw_attr, (classmethod, staticmethod)):
                    meths.add(name)

        return sorted(props), sorted(meths)
