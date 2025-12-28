from __future__ import annotations

from pathlib import Path

import pytest

import synthetic_signal_observatory.config as config_module
from synthetic_signal_observatory.config import load_app_config


def test_load_app_config_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SSO_DISABLE_DOTENV", "1")

    config = load_app_config()

    assert config.db_path == Path("data/sso.duckdb")
    assert config.batch_size == 100
    assert config.seed == 42
    assert config.allow_db_reset is False


def test_load_app_config_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SSO_DISABLE_DOTENV", "1")
    monkeypatch.setenv("SSO_DB_PATH", "data/override.duckdb")
    monkeypatch.setenv("SSO_BATCH_SIZE", "123")
    monkeypatch.setenv("SSO_SEED", "7")
    monkeypatch.setenv("SSO_ALLOW_DB_RESET", "1")

    config = load_app_config()

    assert config.db_path == Path("data/override.duckdb")
    assert config.batch_size == 123
    assert config.seed == 7
    assert config.allow_db_reset is True


@pytest.mark.parametrize(
    "var_name,var_value",
    [
        ("SSO_BATCH_SIZE", "0"),
        ("SSO_BATCH_SIZE", "-5"),
        ("SSO_BATCH_SIZE", "nope"),
        ("SSO_SEED", "0"),
        ("SSO_SEED", "-1"),
        ("SSO_SEED", "nan"),
        ("SSO_ALLOW_DB_RESET", "maybe"),
    ],
)
def test_load_app_config_rejects_invalid_ints(
    monkeypatch: pytest.MonkeyPatch,
    var_name: str,
    var_value: str,
) -> None:
    monkeypatch.setenv("SSO_DISABLE_DOTENV", "1")
    monkeypatch.setenv(var_name, var_value)

    with pytest.raises(ValueError, match=var_name):
        load_app_config()


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("1", True),
        ("true", True),
        ("YES", True),
        ("on", True),
        ("0", False),
        ("false", False),
        ("No", False),
        ("off", False),
    ],
)
def test_load_app_config_parses_allow_db_reset(
    monkeypatch: pytest.MonkeyPatch,
    env_value: str,
    expected: bool,
) -> None:
    monkeypatch.setenv("SSO_DISABLE_DOTENV", "1")
    monkeypatch.setenv("SSO_ALLOW_DB_RESET", env_value)

    config = load_app_config()

    assert config.allow_db_reset is expected


def test_load_app_config_autoloads_dotenv_without_overriding_existing_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SSO_DISABLE_DOTENV", "0")

    # Ensure the process environment does not already have conflicting values.
    for key in ["SSO_DB_PATH", "SSO_SEED", "SSO_ALLOW_DB_RESET"]:
        monkeypatch.delenv(key, raising=False)

    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        """
        # Example dotenv
        SSO_DB_PATH=data/from-dotenv.duckdb
        export SSO_BATCH_SIZE=250
        SSO_SEED='9'
        SSO_ALLOW_DB_RESET=true
        """.strip(),
        encoding="utf-8",
    )

    # Existing env vars should win over dotenv.
    monkeypatch.setenv("SSO_BATCH_SIZE", "999")

    # Point config at our temporary dotenv file.
    monkeypatch.setattr(config_module, "DEFAULT_DOTENV_PATH", dotenv_path)

    config = load_app_config()

    assert config.db_path == Path("data/from-dotenv.duckdb")
    assert config.batch_size == 999
    assert config.seed == 9
    assert config.allow_db_reset is True


# =============================================================================
# Tests for real-time display config (D-0006)
# =============================================================================


def test_load_app_config_defaults_include_realtime_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """New config fields for live mode should have sensible defaults."""
    monkeypatch.setenv("SSO_DISABLE_DOTENV", "1")

    config = load_app_config()

    assert config.auto_refresh_interval == 2
    assert config.auto_run_default is False


def test_load_app_config_parses_auto_refresh_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SSO_AUTO_REFRESH_INTERVAL should be parsed as a positive integer."""
    monkeypatch.setenv("SSO_DISABLE_DOTENV", "1")
    monkeypatch.setenv("SSO_AUTO_REFRESH_INTERVAL", "5")

    config = load_app_config()

    assert config.auto_refresh_interval == 5


def test_load_app_config_rejects_invalid_auto_refresh_interval(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SSO_AUTO_REFRESH_INTERVAL must be a positive integer."""
    monkeypatch.setenv("SSO_DISABLE_DOTENV", "1")
    monkeypatch.setenv("SSO_AUTO_REFRESH_INTERVAL", "0")

    with pytest.raises(ValueError, match="SSO_AUTO_REFRESH_INTERVAL"):
        load_app_config()


@pytest.mark.parametrize(
    "env_value,expected",
    [
        ("1", True),
        ("true", True),
        ("0", False),
        ("false", False),
    ],
)
def test_load_app_config_parses_auto_run_default(
    monkeypatch: pytest.MonkeyPatch,
    env_value: str,
    expected: bool,
) -> None:
    """SSO_AUTO_RUN_DEFAULT should be parsed as a boolean."""
    monkeypatch.setenv("SSO_DISABLE_DOTENV", "1")
    monkeypatch.setenv("SSO_AUTO_RUN_DEFAULT", env_value)

    config = load_app_config()

    assert config.auto_run_default is expected
