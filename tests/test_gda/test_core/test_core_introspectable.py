"""Path: tests/test_gda/test_core/test_core_introspectable.py

Comprehensive unit, regression, and integrity test suite for gda.core.introspectable.

Operational Role:
    Validates IntrospectableMixin and _HybridHelpDescriptor capabilities,
    including public member directory generation (properties, public class
    attributes, and callable methods), property inspection, method signature
    extraction, docstring parsing, class/instance duality, empty/undocumented
    class handling, and defensive error boundaries for unknown or non-string
    member requests.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integrity).
    - Dependencies: Pure in-memory evaluation with zero disk I/O.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

import gda.core.introspectable as intro
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin

if TYPE_CHECKING:
    from tests.test_gda.test_core.conftest import (
        MethodOnlyEntity,
        PropertyOnlyEntity,
        SampleEntity,
    )

__version__ = "1.0.0+build.11"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke contract check verifying public exports and directory output.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_introspectable_exposes_expected_public_interface(
    sample_entity_cls: type[SampleEntity],
) -> None:
    """Verify gda.core.introspectable exports IntrospectableMixin and renders help()."""
    assert set(intro.__all__) == {"IntrospectableMixin"}
    output = sample_entity_cls.help(as_str=True)
    assert output is not None
    assert "=== SampleEntity Public Directory ===" in output


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Directory rendering, property/attribute/method inspection, and MRO discovery.
# ==============================================================================


@pytest.mark.unit
def test_directory_rendering_as_str(sample_entity_cls: type[SampleEntity]) -> None:
    """Verify help() with as_str=True renders formatted public directory including class attributes."""
    output = sample_entity_cls.help(as_str=True)
    assert output is not None
    assert "=== SampleEntity Public Directory ===" in output
    assert "Properties (Attributes & Paths):" in output
    assert "CLASS_CONSTANT" in output
    assert "Class attribute (str)" in output
    assert "display_name" in output
    assert "Return the formatted display name for the entity." in output
    assert "Callable Methods:" in output
    assert "execute_action" in output
    assert "Execute a designated action against the entity." in output


@pytest.mark.unit
def test_directory_rendering_prints_to_stdout(
    sample_entity_cls: type[SampleEntity],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify help() without as_str prints directory directly to standard output."""
    result = sample_entity_cls.help()
    assert result is None

    captured = capsys.readouterr()
    assert "=== SampleEntity Public Directory ===" in captured.out
    assert "display_name" in captured.out
    assert "execute_action" in captured.out


@pytest.mark.regression
def test_introspectable_classmethod_and_staticmethod_discovery() -> None:
    """Verify classmethods and staticmethods appear under callable methods."""

    class AdvancedEntity(IntrospectableMixin):
        @classmethod
        def create_default(cls) -> AdvancedEntity:
            """Factory constructor."""
            return cls()

        @staticmethod
        def calculate_hash(val: str) -> str:
            """Hash calculation."""
            return val.strip()

    _, meths = AdvancedEntity._get_public_members()
    assert "create_default" in meths
    assert "calculate_hash" in meths


@pytest.mark.unit
def test_property_help_on_class(sample_entity_cls: type[SampleEntity]) -> None:
    """Verify property help on class indicates unbound status."""
    output = sample_entity_cls.help("display_name", as_str=True)
    assert output is not None
    assert "Help on property 'SampleEntity.display_name':" in output
    assert (
        "Current Value: <Unbound property: call help() on an instance to inspect value>" in output
    )
    assert "Description:   Return the formatted display name for the entity." in output


@pytest.mark.unit
def test_property_help_on_instance(sample_entity: SampleEntity) -> None:
    """Verify property help on instance evaluates and prints current value."""
    sample_entity._name = "ActiveNode"
    output = sample_entity.help("display_name", as_str=True)
    assert output is not None
    assert "Help on property 'SampleEntity.display_name':" in output
    assert "Current Value: Entity:ActiveNode" in output
    assert "Description:   Return the formatted display name for the entity." in output


@pytest.mark.unit
def test_plain_attribute_help_on_class(sample_entity_cls: type[SampleEntity]) -> None:
    """Verify help on plain non-callable class attribute renders value and type."""
    output = sample_entity_cls.help("CLASS_CONSTANT", as_str=True)
    assert output is not None
    assert "Help on attribute 'SampleEntity.CLASS_CONSTANT':" in output
    assert "Value: plain_non_callable_attribute" in output
    assert "Type:  str" in output


@pytest.mark.regression
def test_introspectable_inherited_member_override() -> None:
    """Verify subclass override docstring is rendered instead of parent docstring."""

    class BaseItem(IntrospectableMixin):
        @property
        def description(self) -> str:
            """Base description."""
            return "base"

    class DerivedItem(BaseItem):
        @property
        def description(self) -> str:
            """Derived custom description."""
            return "derived"

    output = DerivedItem.help("description", as_str=True)
    assert output is not None
    assert "Derived custom description." in output


@pytest.mark.unit
def test_method_help_on_class(sample_entity_cls: type[SampleEntity]) -> None:
    """Verify method help on class extracts signature and full docstring."""
    output = sample_entity_cls.help("execute_action", as_str=True)
    assert output is not None
    assert "Help on method 'SampleEntity.execute_action':" in output
    assert "Signature:   execute_action" in output
    assert "action_name" in output
    assert "Args:" in output
    assert "action_name: The name of the action to execute." in output


@pytest.mark.unit
def test_method_help_on_instance_binds_signature(sample_entity: SampleEntity) -> None:
    """Verify method help on instance extracts bound signature omitting self."""
    output = sample_entity.help("execute_action", as_str=True)
    assert output is not None
    assert "Help on method 'SampleEntity.execute_action':" in output
    assert "Signature:   execute_action" in output
    assert "action_name" in output


@pytest.mark.unit
def test_method_help_prints_to_stdout(
    sample_entity_cls: type[SampleEntity],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify method help without as_str prints directly to standard output."""
    result = sample_entity_cls.help("simple_action")
    assert result is None

    captured = capsys.readouterr()
    assert "Help on method 'SampleEntity.simple_action':" in captured.out
    assert "Execute a simple parameterless action." in captured.out


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Empty/partial classes, undocumented members, and signature fallbacks.
# ==============================================================================


@pytest.mark.unit
def test_directory_rendering_with_no_properties(
    method_only_cls: type[MethodOnlyEntity],
) -> None:
    """Verify help() directory omits Properties section when none exist."""
    output = method_only_cls.help(as_str=True)
    assert output is not None
    assert "Properties (Attributes & Paths):" not in output
    assert "Callable Methods:" in output
    assert "only_method" in output


@pytest.mark.unit
def test_directory_rendering_with_no_methods(
    property_only_cls: type[PropertyOnlyEntity],
) -> None:
    """Verify help() directory omits Callable Methods section when none exist."""
    output = property_only_cls.help(as_str=True)
    assert output is not None
    assert "Properties (Attributes & Paths):" in output
    assert "only_property" in output
    assert "Callable Methods:" not in output


@pytest.mark.regression
def test_directory_rendering_on_empty_class_omits_both_sections(
    empty_entity_cls: type[IntrospectableMixin],
) -> None:
    """Verify help() on a class with no public members omits both sections."""
    output = empty_entity_cls.help(as_str=True)
    assert output is not None
    assert f"=== {empty_entity_cls.__name__} Public Directory ===" in output
    assert "Properties (Attributes & Paths):" not in output
    assert "Callable Methods:" not in output
    assert "Tip: Call .help('name')" in output


@pytest.mark.regression
def test_undocumented_members_use_fallback_descriptions(
    undocumented_entity_cls: type[IntrospectableMixin],
) -> None:
    """Verify undocumented properties and methods render clean fallback text."""
    directory = undocumented_entity_cls.help(as_str=True)
    assert directory is not None
    assert "No description available." in directory

    props, meths = undocumented_entity_cls._get_public_members()
    for member in (*props, *meths):
        detail = undocumented_entity_cls.help(member, as_str=True)
        assert detail is not None
        assert "No documentation provided." in detail


@pytest.mark.regression
def test_method_help_signature_fallback_on_uninspectable_callable(
    sample_entity_cls: type[SampleEntity],
) -> None:
    """Verify signature fallback '(...)' when inspect.signature raises ValueError."""
    with patch("inspect.signature", side_effect=ValueError("Cannot inspect signature")):
        output = sample_entity_cls.help("simple_action", as_str=True)
        assert output is not None
        assert "Signature:   simple_action(...)" in output


@pytest.mark.regression
def test_whitespace_member_name_falls_back_to_directory(
    sample_entity_cls: type[SampleEntity],
) -> None:
    """Verify whitespace member_name falls back cleanly to directory output."""
    output = sample_entity_cls.help("   ", as_str=True)
    assert output is not None
    assert "=== SampleEntity Public Directory ===" in output


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Failing properties, unknown members, and non-string member_name.
# ==============================================================================


@pytest.mark.regression
def test_failing_property_help_on_instance_catches_exception(
    sample_entity: SampleEntity,
) -> None:
    """Verify property raising an exception during evaluation formats error cleanly."""
    output = sample_entity.help("failing_property", as_str=True)
    assert output is not None
    assert "Help on property 'SampleEntity.failing_property':" in output
    assert "<Error evaluating: Property calculation failed>" in output


@pytest.mark.regression
def test_unknown_member_raises_genealogy_desk_error(
    sample_entity_cls: type[SampleEntity],
) -> None:
    """Verify querying non-existent member raises GenealogyDeskError."""
    with pytest.raises(GenealogyDeskError) as exc_info:
        sample_entity_cls.help("non_existent_method")

    assert exc_info.value.error_code == "ERR_MEMBER_NOT_FOUND"
    assert "non_existent_method" in exc_info.value.message
    assert exc_info.value.details == {
        "class": "SampleEntity",
        "member": "non_existent_method",
    }


@pytest.mark.regression
@pytest.mark.parametrize("bad_member_name", [123, ["display_name"], True])
def test_non_string_member_name_raises_genealogy_desk_error(
    sample_entity_cls: type[SampleEntity],
    bad_member_name: Any,
) -> None:
    """Verify non-string member_name raises GenealogyDeskError instead of AttributeError."""
    with pytest.raises(GenealogyDeskError):
        sample_entity_cls.help(bad_member_name)


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Deterministic sorting and private/help filtering in _get_public_members.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_get_public_members_filters_private_and_returns_sorted_lists(
    sample_entity_cls: type[SampleEntity],
) -> None:
    """Verify _get_public_members includes public class attributes and filters private/help names."""
    props, meths = sample_entity_cls._get_public_members()

    assert props == sorted(props)
    assert meths == sorted(meths)
    assert "CLASS_CONSTANT" in props
    assert "display_name" in props
    assert "failing_property" in props
    assert "execute_action" in meths
    assert "simple_action" in meths
    assert "_internal_helper" not in props
    assert "_internal_helper" not in meths
    assert "CLASS_CONSTANT" not in meths
    assert "help" not in props
    assert "help" not in meths
