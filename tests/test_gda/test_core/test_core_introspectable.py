"""Path: tests/test_gda/test_core/test_core_introspectable.py

Unit verification suite for GDA Core runtime introspection mixin.

Operational Role:
    Validates IntrospectableMixin and _HybridHelpDescriptor capabilities,
    including public member directory generation, property inspection,
    method signature extraction, docstring parsing, class/instance duality,
    and defensive error boundaries for unknown member requests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin

if TYPE_CHECKING:
    from tests.test_gda.test_core.conftest import (
        MethodOnlyEntity,
        PropertyOnlyEntity,
        SampleEntity,
    )

__version__ = "1.0.0+build.7"

# ==============================================================================
# GROUP 1: PUBLIC DIRECTORY DISCOVERY
# Note: Validates member categorization and high-level directory rendering
# ==============================================================================


@pytest.mark.unit
def test_get_public_members_filters_private_and_help(
    sample_entity_cls: type[SampleEntity],
) -> None:
    """Verify _get_public_members discovers only public properties and methods."""
    props, meths = sample_entity_cls._get_public_members()

    assert "display_name" in props
    assert "failing_property" in props
    assert "_internal_helper" not in props
    assert "_internal_helper" not in meths
    assert "CLASS_CONSTANT" not in props
    assert "CLASS_CONSTANT" not in meths
    assert "help" not in props
    assert "help" not in meths
    assert "execute_action" in meths
    assert "simple_action" in meths


@pytest.mark.unit
def test_directory_rendering_as_str(sample_entity_cls: type[SampleEntity]) -> None:
    """Verify help() with as_str=True renders formatted public directory."""
    output = sample_entity_cls.help(as_str=True)
    assert output is not None
    assert "=== SampleEntity Public Directory ===" in output
    assert "Properties (Attributes & Paths):" in output
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
def test_introspectable_classmethod_and_staticmethod_discovery() -> None:
    """Verify classmethods and staticmethods appear under callable methods (INT-001)."""

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


# ==============================================================================
# GROUP 2: PROPERTY INTROSPECTION
# Note: Validates inspection of properties on classes and live instances
# ==============================================================================


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


@pytest.mark.regression
def test_failing_property_help_on_instance_catches_exception(
    sample_entity: SampleEntity,
) -> None:
    """Verify property raising an exception during evaluation formats error cleanly."""
    output = sample_entity.help("failing_property", as_str=True)
    assert output is not None
    assert "Help on property 'SampleEntity.failing_property':" in output
    assert "<Error evaluating: Property calculation failed>" in output


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
    """Verify subclass override docstring is rendered instead of parent docstring (INT-002)."""

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


# ==============================================================================
# GROUP 3: METHOD INTROSPECTION
# Note: Validates signature extraction and docstring inspection
# ==============================================================================


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
def test_method_help_on_instance_binds_signature(
    sample_entity: SampleEntity,
) -> None:
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


@pytest.mark.regression
def test_method_help_signature_fallback_on_uninspectable_callable(
    sample_entity_cls: type[SampleEntity],
) -> None:
    """Verify signature fallback '( ... )' when inspect.signature raises ValueError."""
    with patch("inspect.signature", side_effect=ValueError("Cannot inspect signature")):
        output = sample_entity_cls.help("simple_action", as_str=True)
    assert output is not None
    assert "Signature:   simple_action(...)" in output


# ==============================================================================
# GROUP 4: DEFENSIVE ERROR BOUNDARIES
# Note: Validates unknown member and whitespace handling
# ==============================================================================


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
def test_whitespace_member_name_falls_back_to_directory(
    sample_entity_cls: type[SampleEntity],
) -> None:
    """Verify whitespace member_name falls back cleanly to directory output."""
    output = sample_entity_cls.help("   ", as_str=True)
    assert output is not None
    assert "=== SampleEntity Public Directory ===" in output
