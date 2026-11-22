"""Path: tests/test_gen_desk_tools/test_metrics/test_config_group_4_5_6.py

Error handling, 4-tier logging, runtime discovery, and invariants for gd_metrics config.

Operational Role:
    Verifies validation failures (ValueError vs. KeyError), malformed/unreadable
    TOML handling, 4-tier logging (ERROR, INFO, VERBOSE, DEBUG), live
    cwd/os.environ resolution, and dataclass immutability invariants in
    gen_desk_tools.metrics.config.
"""

from __future__ import annotations

import dataclasses
import logging
import tomllib
from pathlib import Path

import pytest

from gen_desk_tools.metrics.config import (
    DEFAULT_COVERAGE_GATES,
    VALID_SCOPES,
    BatchDefinition,
    load_config,
    resolve_batches,
)

__version__ = "1.0.0+build.2"

_CONFIG_LOGGER = "gen_desk_tools.metrics.config"


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Invalid values (ValueError), unknown keys (KeyError), and bad files.
# ==========================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_bool", ["maybe", "2", "@", "yes!"])
def test_load_config_invalid_bool_env_raises_value_error(tmp_path: Path, bad_bool: str) -> None:
    """Verify unrecognized GDA_METRICS_SYNC_SHEETS tokens raise ValueError."""
    with pytest.raises(ValueError, match="Invalid boolean value"):
        load_config(workspace_root=tmp_path, env={"GDA_METRICS_SYNC_SHEETS": bad_bool})


@pytest.mark.regression
def test_load_config_invalid_scope_raises_value_error(tmp_path: Path) -> None:
    """Verify unsupported scope name raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported scope"):
        load_config(workspace_root=tmp_path, env={}, cli_scopes=("unknown",))


@pytest.mark.regression
def test_resolve_batches_unknown_batch_id_raises_value_error(tmp_path: Path) -> None:
    """Verify requesting an unknown batch ID raises ValueError."""
    cfg = load_config(workspace_root=tmp_path, env={}, cli_batches=("NO-SUCH-BATCH",))

    with pytest.raises(ValueError, match="Unknown batch ID"):
        resolve_batches(cfg)


@pytest.mark.regression
def test_load_config_malformed_toml_raises_decode_error(tmp_path: Path) -> None:
    """Verify invalid TOML syntax in a config file raises TOMLDecodeError."""
    bad_toml = tmp_path / "broken.toml"
    bad_toml.write_text(
        "[metrics.gates.coverage]\ngda = @\nsystem =\n",
        encoding="utf-8",
    )

    with pytest.raises(tomllib.TOMLDecodeError):
        load_config(workspace_root=tmp_path, config_path=bad_toml, env={})


@pytest.mark.regression
def test_load_config_invalid_coverage_gate_type_raises_value_error(tmp_path: Path) -> None:
    """Verify non-numeric coverage gate values raise ValueError during float coercion."""
    bad_gate_toml = tmp_path / "bad_gate.toml"
    bad_gate_toml.write_text(
        '[gates.coverage]\ngda = "@"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_config(workspace_root=tmp_path, config_path=bad_gate_toml, env={})


@pytest.mark.regression
def test_load_config_unknown_telemetry_setting_name_raises_key_error(tmp_path: Path) -> None:
    """Verify an unrecognized setting name under [telemetry] raises KeyError."""
    unknown_key_toml = tmp_path / "unknown_key.toml"
    unknown_key_toml.write_text(
        "[telemetry]\nsync_shets_by_default = false\n",
        encoding="utf-8",
    )

    with pytest.raises(KeyError, match="sync_shets_by_default"):
        load_config(workspace_root=tmp_path, config_path=unknown_key_toml, env={})


@pytest.mark.regression
def test_load_config_unknown_env_setting_name_raises_key_error(tmp_path: Path) -> None:
    """Verify an unrecognized GDA_METRICS_* environment variable raises KeyError."""
    with pytest.raises(KeyError, match="GDA_METRICS_UNKNOWN_FLAG"):
        load_config(workspace_root=tmp_path, env={"GDA_METRICS_UNKNOWN_FLAG": "1"})


@pytest.mark.regression
@pytest.mark.integration
def test_load_config_directory_path_raises_os_error(tmp_path: Path) -> None:
    """Verify passing a directory as config_path raises OSError."""
    # Point config_path at a directory so file read fails consistently across OSes.
    blocked_dir = tmp_path / "not_a_file.toml"
    blocked_dir.mkdir()

    with pytest.raises(OSError):
        load_config(workspace_root=tmp_path, config_path=blocked_dir, env={})


@pytest.mark.regression
@pytest.mark.integration
def test_load_config_binary_non_utf8_file_raises_unicode_decode_error(tmp_path: Path) -> None:
    """Verify reading a binary or non-UTF-8 config file raises UnicodeDecodeError."""
    binary_cfg = tmp_path / "corrupt.toml"
    binary_cfg.write_bytes(b"\xff\xfe\x00\x01")

    with pytest.raises(UnicodeDecodeError):
        load_config(workspace_root=tmp_path, config_path=binary_cfg, env={})


@pytest.mark.regression
def test_parse_batches_missing_required_keys_raises_key_error(tmp_path: Path) -> None:
    """Verify [[batches]] entries missing required id or scope keys raise KeyError."""
    bad_batch_toml = tmp_path / "missing_keys.toml"
    bad_batch_toml.write_text(
        '[[batches]]\nid = "B1"\npaths = ["src/gda"]\n',
        encoding="utf-8",
    )

    with pytest.raises(KeyError):
        load_config(workspace_root=tmp_path, config_path=bad_batch_toml, env={})


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: Live cwd/os.environ discovery and 4-tier logging emission via caplog.
# ==========================================================================


@pytest.mark.integration
def test_load_config_defaults_to_cwd_and_os_environ_when_omitted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify load_config resolves Path.cwd() and os.environ when args are None."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GDA_METRICS_SCOPE", "system")
    monkeypatch.setenv("GDA_METRICS_SYNC_SHEETS", "false")

    cfg = load_config()

    assert cfg.workspace_root == tmp_path.resolve()
    assert cfg.scopes == ("system",)
    assert cfg.sync_sheets is False


@pytest.mark.integration
def test_load_config_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify load_config emits INFO, VERBOSE, and DEBUG records during resolution."""
    with caplog.at_level(logging.DEBUG, logger=_CONFIG_LOGGER):
        load_config(workspace_root=tmp_path, env={})

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)


@pytest.mark.regression
@pytest.mark.integration
def test_load_config_emits_error_log_record_on_validation_failure(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify load_config logs an ERROR record before raising on invalid input."""
    with caplog.at_level(logging.ERROR, logger=_CONFIG_LOGGER):
        with pytest.raises(ValueError, match="Invalid boolean value"):
            load_config(workspace_root=tmp_path, env={"GDA_METRICS_SYNC_SHEETS": "maybe"})

    assert any(record.levelname == "ERROR" for record in caplog.records)


# ==========================================================================
# GROUP 6: Integrity & Invariants
# Note: Dataclass immutability and scope/coverage-gate key parity.
# ==========================================================================


@pytest.mark.integrity
def test_metrics_config_and_batch_definition_are_immutable(tmp_path: Path) -> None:
    """Verify MetricsConfig and BatchDefinition reject in-place mutation."""
    cfg = load_config(workspace_root=tmp_path, env={})
    batch = BatchDefinition(
        id="GDA-Batch-1",
        scope="gda",
        tier="Tier 0",
        paths=("src/gda/core",),
        test_paths=("tests/test_gda/test_core",),
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.sync_sheets = False  # type: ignore[misc]

    with pytest.raises(dataclasses.FrozenInstanceError):
        batch.id = "MUTATED"  # type: ignore[misc]


@pytest.mark.integrity
def test_default_coverage_gates_keys_are_subset_of_valid_scopes() -> None:
    """Verify every subsystem key in DEFAULT_COVERAGE_GATES is in VALID_SCOPES."""
    assert set(DEFAULT_COVERAGE_GATES).issubset(VALID_SCOPES)
