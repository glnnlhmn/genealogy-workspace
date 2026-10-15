# Name: introspectable.py
# Path: src/gda/core/introspectable.py
# Version: 1.0.0+build.r4

"""Provide centralized runtime introspection mixin for self-documenting archive components.

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

__version__ = "1.0.0+build.r4"


class _HybridHelpDescriptor:
    """Enable .help() to function seamlessly as both a classmethod and an instancemethod."""

    def __get__(self, instance: Any, owner: type) -> Callable[..., str | None]:
        """Bind the introspection dispatcher to the target class or instance.

        Args:
            instance: Active instance invoking help(), or None if called on the class.
            owner: Class type declaring or inheriting IntrospectableMixin.

        Returns:
            Callable dispatcher executing member inspection or public directory listing.
        """

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
            cls = owner

            if member_name and member_name.strip():
                clean_name = member_name.strip()
                cls_attr = getattr(cls, clean_name, None)
                if cls_attr is None:
                    raise GenealogyDeskError(
                        f"'{clean_name}' is not a recognized member of {cls.__name__}.",
                        error_code="ERR_MEMBER_NOT_FOUND",
                        details={"class": cls.__name__, "member": clean_name},
                    )

                output_lines: list[str] = []
                if isinstance(cls_attr, property):
                    doc = inspect.getdoc(cls_attr.fget) or "No documentation provided."
                    if instance is not None:
                        try:
                            current_val = getattr(instance, clean_name)
                        except Exception as err:
                            current_val = f"<Error evaluating: {err}>"
                    else:
                        current_val = "<Unbound property: call help() on an instance to inspect value>"

                    output_lines.append(
                        f"\nHelp on property '{cls.__name__}.{clean_name}':"
                    )
                    output_lines.append(f"  Current Value: {current_val}")
                    output_lines.append(f"  Description:   {doc}\n")
                elif callable(cls_attr):
                    doc = inspect.getdoc(cls_attr) or "No documentation provided."
                    target_callable = (
                        getattr(instance, clean_name)
                        if instance is not None
                        else cls_attr
                    )
                    try:
                        sig = inspect.signature(target_callable)
                    except (ValueError, TypeError):
                        sig = "(...)"  # type: ignore[assignment]
                    output_lines.append(
                        f"\nHelp on method '{cls.__name__}.{clean_name}':"
                    )
                    output_lines.append(f"  Signature:   {clean_name}{sig}")
                    output_lines.append(f"  Description: {doc}\n")
                else:
                    output_lines.append(
                        f"\nHelp on attribute '{cls.__name__}.{clean_name}':"
                    )
                    output_lines.append(f"  Value: {cls_attr}")
                    output_lines.append(f"  Type:  {type(cls_attr).__name__}\n")

                result = "\n".join(output_lines)
                if as_str:
                    return result
                print(result)
                return None

            # Render full directory
            props, meths = cls._get_public_members()
            lines = [f"\n=== {cls.__name__} Public Directory ==="]

            if props:
                lines.append("\nProperties (Attributes & Paths):")
                for p in props:
                    prop_obj = getattr(cls, p, None)
                    doc = (
                        inspect.getdoc(prop_obj.fget)
                        if isinstance(prop_obj, property)
                        else None
                    )
                    first_line = (
                        doc.split("\n")[0] if doc else "No description available."
                    )
                    lines.append(f"  • {p:<25} - {first_line}")

            if meths:
                lines.append("\nCallable Methods:")
                for m in meths:
                    meth_obj = getattr(cls, m, None)
                    doc = inspect.getdoc(meth_obj) if callable(meth_obj) else None
                    first_line = (
                        doc.split("\n")[0] if doc else "No description available."
                    )
                    lines.append(f"  • {m:<25} - {first_line}")

            lines.append(
                "\nTip: Call .help('name') on your instance or class for full details.\n"
            )
            result = "\n".join(lines)
            if as_str:
                return result
            print(result)
            return None

        return help_dispatcher


class IntrospectableMixin:
    """Provide dual class- and instance-level runtime directory inspection.

    Subclasses inherit the self-documenting .help() method, allowing operators
    to inspect public properties, methods, call signatures, and docstring contracts
    in interactive REPL sessions or CLI utilities.

    Attributes:
        help: Descriptor dispatcher providing indexed directory output or detailed member help.
    """

    help = _HybridHelpDescriptor()

    @classmethod
    def _get_public_members(cls) -> tuple[list[str], list[str]]:
        """Discover and categorize public properties and callable methods on the class.

        Returns:
            Tuple containing a sorted list of property names and a sorted list of callable method names.
        """
        properties: list[str] = []
        methods: list[str] = []

        for name in dir(cls):
            if name.startswith("_") or name == "help":
                continue

            attr_class_level = getattr(cls, name, None)
            if isinstance(attr_class_level, property):
                properties.append(name)
            elif callable(attr_class_level):
                methods.append(name)

        return sorted(properties), sorted(methods)
