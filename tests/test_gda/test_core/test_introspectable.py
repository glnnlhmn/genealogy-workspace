# Name: test_introspectable.py
# Path: tests/test_gda/test_core/test_introspectable.py
# Version: 1.0.0+build.r4

"""Unit verification suite for GDA Core runtime introspection mixin.

Operational Role:
    Validates IntrospectableMixin and _HybridHelpDescriptor capabilities,
    including public member directory generation, property inspection,
    method signature extraction, docstring parsing, class/instance duality,
    and defensive error boundaries for unknown member requests.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral assertion mapping across introspection contracts.
    - Fully decorated: @pytest.mark.unit and @pytest.mark.smoke applied throughout.
    - Dependencies: pytest standard library fixtures only (zero disk I/O).
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin

__version__ = "1.0.0+build.r4"

# ==============================================================================
# TEST FIXTURE CLASSES
# Note: Sample domain stubs used strictly for introspection contract testing
# ==============================================================================


class SampleEntity(IntrospectableMixin):
    """A sample entity demonstrating properties and methods for introspection."""

    CLASS_CONSTANT = "plain_non_callable_attribute"

    def __init__(self, name: str = "TestItem", count: int = 10) -> None:
        """Initialize SampleEntity."""
        self._name = name
        self.count = count

    @property
    def display_name(self) -> str:
        """Return the formatted display name for the entity."""
        return f"Entity:{self._name}"

    @property
    def failing_property(self) -> str:
        """Raise an intentional runtime error during property access."""
        raise RuntimeError("Property calculation failed")

    def execute_action(self, action_name: str, force: bool = False) -> bool:
        """Execute a designated action against the entity.

        Args:
            action_name: The name of the action to execute.
            force: If True, bypass safety constraints.

        Returns:
            True if action executed successfully.
        """
        return bool(action_name and force)

    def simple_action(self) -> None:
        """Execute a simple parameterless action."""
        return None

    def _internal_helper(self) -> None:
        """Private helper that should not appear in public directories."""
        return None


class MethodOnlyEntity(IntrospectableMixin):
    """An entity containing only callable methods without properties."""

    def only_method(self) -> str:
        """Execute the lone method."""
        return "ok"


class PropertyOnlyEntity(IntrospectableMixin):
    """An entity containing only properties without methods."""

    @property
    def only_property(self) -> str:
        """Return lone property."""
        return "val"


# ==============================================================================
# GROUP 1: PUBLIC DIRECTORY DISCOVERY
# Note: Validates member categorization and high-level directory rendering
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_get_public_members_filters_private_and_help() -> None:
    """Verify _get_public_members discovers only public properties and methods."""
    props, meths = SampleEntity._get_public_members()

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
def test_directory_rendering_as_str() -> None:
    """Verify help() with as_str=True renders formatted public directory."""
    output = SampleEntity.help(as_str=True)
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
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify help() without as_str prints directory directly to standard output."""
    result = SampleEntity.help()
    assert result is None

    captured = capsys.readouterr()
    assert "=== SampleEntity Public Directory ===" in captured.out
    assert "display_name" in captured.out
    assert "execute_action" in captured.out


@pytest.mark.unit
def test_directory_rendering_with_no_properties() -> None:
    """Verify help() directory omits Properties section when none exist."""
    output = MethodOnlyEntity.help(as_str=True)
    assert output is not None
    assert "Properties (Attributes & Paths):" not in output
    assert "Callable Methods:" in output
    assert "only_method" in output


@pytest.mark.unit
def test_directory_rendering_with_no_methods() -> None:
    """Verify help() directory omits Callable Methods section when none exist."""
    output = PropertyOnlyEntity.help(as_str=True)
    assert output is not None
    assert "Properties (Attributes & Paths):" in output
    assert "only_property" in output
    assert "Callable Methods:" not in output


# ==============================================================================
# GROUP 2: PROPERTY INTROSPECTION
# Note: Validates inspection of properties on classes and live instances
# ==============================================================================


@pytest.mark.unit
def test_property_help_on_class() -> None:
    """Verify property help on class indicates unbound status."""
    output = SampleEntity.help("display_name", as_str=True)
    assert output is not None
    assert "Help on property 'SampleEntity.display_name':" in output
    assert (
        "Current Value: <Unbound property: call help() on an instance to inspect value>"
        in output
    )
    assert "Description:   Return the formatted display name for the entity." in output


@pytest.mark.unit
def test_property_help_on_instance() -> None:
    """Verify property help on instance evaluates and prints current value."""
    entity = SampleEntity(name="ActiveNode")
    output = entity.help("display_name", as_str=True)
    assert output is not None
    assert "Help on property 'SampleEntity.display_name':" in output
    assert "Current Value: Entity:ActiveNode" in output
    assert "Description:   Return the formatted display name for the entity." in output


@pytest.mark.unit
def test_failing_property_help_on_instance_catches_exception() -> None:
    """Verify property raising an exception during evaluation formats error cleanly."""
    entity = SampleEntity()
    output = entity.help("failing_property", as_str=True)
    assert output is not None
    assert "Help on property 'SampleEntity.failing_property':" in output
    assert "<Error evaluating: Property calculation failed>" in output


@pytest.mark.unit
def test_plain_attribute_help_on_class() -> None:
    """Verify help on plain non-callable class attribute renders value and type."""
    output = SampleEntity.help("CLASS_CONSTANT", as_str=True)
    assert output is not None
    assert "Help on attribute 'SampleEntity.CLASS_CONSTANT':" in output
    assert "Value: plain_non_callable_attribute" in output
    assert "Type:  str" in output


# ==============================================================================
# GROUP 3: METHOD INTROSPECTION
# Note: Validates signature extraction and docstring inspection
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_method_help_on_class() -> None:
    """Verify method help on class extracts signature and full docstring."""
    output = SampleEntity.help("execute_action", as_str=True)
    assert output is not None
    assert "Help on method 'SampleEntity.execute_action':" in output
    assert "Signature:   execute_action" in output
    assert "action_name" in output
    assert "Args:" in output
    assert "action_name: The name of the action to execute." in output


@pytest.mark.unit
def test_method_help_on_instance_binds_signature() -> None:
    """Verify method help on instance extracts bound signature omitting self."""
    entity = SampleEntity()
    output = entity.help("execute_action", as_str=True)
    assert output is not None
    assert "Help on method 'SampleEntity.execute_action':" in output
    assert "Signature:   execute_action" in output
    assert "action_name" in output


@pytest.mark.unit
def test_method_help_prints_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify method help without as_str prints directly to standard output."""
    result = SampleEntity.help("simple_action")
    assert result is None

    captured = capsys.readouterr()
    assert "Help on method 'SampleEntity.simple_action':" in captured.out
    assert "Execute a simple parameterless action." in captured.out


@pytest.mark.unit
def test_method_help_signature_fallback_on_uninspectable_callable() -> None:
    """Verify signature fallback '( ... )' when inspect.signature raises ValueError."""
    with patch("inspect.signature", side_effect=ValueError("Cannot inspect signature")):
        output = SampleEntity.help("simple_action", as_str=True)
    assert output is not None
    assert "Signature:   simple_action(...)" in output


# ==============================================================================
# GROUP 4: DEFENSIVE ERROR BOUNDARIES
# Note: Validates unknown member and whitespace handling
# ==============================================================================


@pytest.mark.unit
def test_unknown_member_raises_genealogy_desk_error() -> None:
    """Verify querying non-existent member raises GenealogyDeskError."""
    with pytest.raises(GenealogyDeskError) as exc_info:
        SampleEntity.help("non_existent_method")

    assert exc_info.value.error_code == "ERR_MEMBER_NOT_FOUND"
    assert "non_existent_method" in exc_info.value.message
    assert exc_info.value.details == {
        "class": "SampleEntity",
        "member": "non_existent_method",
    }


@pytest.mark.unit
def test_whitespace_member_name_falls_back_to_directory() -> None:
    """Verify whitespace member_name falls back cleanly to directory output."""
    output = SampleEntity.help("   ", as_str=True)
    assert output is not None
    assert "=== SampleEntity Public Directory ===" in output
