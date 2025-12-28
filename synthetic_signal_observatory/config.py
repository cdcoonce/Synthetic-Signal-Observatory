"""Centralized, environment-aware configuration.

This module keeps configuration values (db path, batch size, seed) in one place.
It is intentionally small and dependency-free.

Notes
-----
- Configuration is read at runtime (not import time) to keep Streamlit reruns
  predictable.
- Environment variables are optional overrides.

Environment Variables
---------------------
- ``SSO_DB_PATH``: Path to the DuckDB file. Default: ``data/sso.duckdb``
- ``SSO_BATCH_SIZE``: Number of events generated per click. Default: ``100``
- ``SSO_SEED``: RNG seed used for synthetic generation. Default: ``42``
- ``SSO_ALLOW_DB_RESET``: Enable destructive reset UI. Default: ``0``
- ``SSO_DISABLE_DOTENV``: Disable auto-loading repo-root ``.env``. Default: ``0``
- ``SSO_AUTO_REFRESH_INTERVAL``: Live mode refresh interval in seconds. Default: ``2``
- ``SSO_AUTO_RUN_DEFAULT``: Whether live mode is on by default. Default: ``0``
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


DEFAULT_DOTENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def _strip_wrapping_quotes(value: str) -> str:
    """Strip a single pair of wrapping quotes.

    Parameters
    ----------
    value:
        Raw value string.

    Returns
    -------
    str
        Value with a single layer of matching wrapping quotes removed.
    """

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _read_dotenv_if_present(dotenv_path: Path) -> dict[str, str]:
    """Read a `.env` file into a mapping.

    This is intentionally small and dependency-free (no python-dotenv).

    Rules
    -----
    - Missing file: returns an empty mapping.
    - Supports lines of the form: `KEY=VALUE` (optionally prefixed with `export `).
    - Ignores blank lines and `#` comments.

    Parameters
    ----------
    dotenv_path:
        Path to the `.env` file.
    """

    if not dotenv_path.exists():
        return {}

    if not dotenv_path.is_file():
        raise ValueError(f"dotenv path is not a file: {dotenv_path}")

    parsed: dict[str, str] = {}

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        value = _strip_wrapping_quotes(value.strip())

        parsed[key] = value

    logger.info("Read dotenv file: %s", dotenv_path)
    return parsed


def _get_config_value(
    key: str,
    *,
    dotenv_values: dict[str, str],
    default: str,
) -> str:
    """Return a config value with precedence: env > dotenv > default."""

    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    if key in dotenv_values:
        return dotenv_values[key]
    return default


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Runtime configuration for the Streamlit app.

    Parameters
    ----------
    db_path:
        Path to the DuckDB database file.
    batch_size:
        Number of events to generate per UI action.
    seed:
        Random seed for deterministic synthetic generation.
    allow_db_reset:
        Whether destructive database reset controls are enabled in the UI.
        This MUST default to False.
    """

    db_path: Path
    batch_size: int
    seed: int
    allow_db_reset: bool
    auto_refresh_interval: int
    auto_run_default: bool


def _parse_bool(env_value: str, *, var_name: str) -> bool:
    """Parse a boolean environment variable.

    Parameters
    ----------
    env_value:
        Raw environment variable value.
    var_name:
        Environment variable name (for error messages).

    Returns
    -------
    bool
        Parsed boolean.

    Raises
    ------
    ValueError
        If the value is not recognized.
    """

    normalized = env_value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"{var_name} must be a boolean, got {env_value!r}")


def _parse_positive_int(env_value: str, *, var_name: str) -> int:
    """Parse and validate a positive integer.

    Parameters
    ----------
    env_value:
        Raw environment variable value.
    var_name:
        Environment variable name (for error messages).

    Returns
    -------
    int
        Parsed integer.

    Raises
    ------
    ValueError
        If the value is not a positive integer.
    """

    try:
        parsed = int(env_value)
    except ValueError as exc:
        raise ValueError(f"{var_name} must be an integer, got {env_value!r}") from exc

    if parsed <= 0:
        raise ValueError(f"{var_name} must be > 0, got {parsed}")

    return parsed


def load_app_config() -> AppConfig:
    """Load application configuration.

    Environment variables override defaults.

    Returns
    -------
    AppConfig
        Loaded configuration.
    """

    disable_dotenv = _parse_bool(
        os.getenv("SSO_DISABLE_DOTENV", "0"),
        var_name="SSO_DISABLE_DOTENV",
    )
    dotenv_values = {} if disable_dotenv else _read_dotenv_if_present(DEFAULT_DOTENV_PATH)

    db_path_str = _get_config_value(
        "SSO_DB_PATH",
        dotenv_values=dotenv_values,
        default="data/sso.duckdb",
    )
    batch_size_str = _get_config_value(
        "SSO_BATCH_SIZE",
        dotenv_values=dotenv_values,
        default="100",
    )
    seed_str = _get_config_value(
        "SSO_SEED",
        dotenv_values=dotenv_values,
        default="42",
    )
    allow_db_reset_str = _get_config_value(
        "SSO_ALLOW_DB_RESET",
        dotenv_values=dotenv_values,
        default="0",
    )
    auto_refresh_interval_str = _get_config_value(
        "SSO_AUTO_REFRESH_INTERVAL",
        dotenv_values=dotenv_values,
        default="2",
    )
    auto_run_default_str = _get_config_value(
        "SSO_AUTO_RUN_DEFAULT",
        dotenv_values=dotenv_values,
        default="0",
    )

    config = AppConfig(
        db_path=Path(db_path_str),
        batch_size=_parse_positive_int(batch_size_str, var_name="SSO_BATCH_SIZE"),
        seed=_parse_positive_int(seed_str, var_name="SSO_SEED"),
        allow_db_reset=_parse_bool(
            allow_db_reset_str,
            var_name="SSO_ALLOW_DB_RESET",
        ),
        auto_refresh_interval=_parse_positive_int(
            auto_refresh_interval_str,
            var_name="SSO_AUTO_REFRESH_INTERVAL",
        ),
        auto_run_default=_parse_bool(
            auto_run_default_str,
            var_name="SSO_AUTO_RUN_DEFAULT",
        ),
    )

    logger.info(
        "Loaded app config: db_path=%s batch_size=%s seed=%s allow_db_reset=%s "
        "auto_refresh_interval=%s auto_run_default=%s",
        config.db_path,
        config.batch_size,
        config.seed,
        config.allow_db_reset,
        config.auto_refresh_interval,
        config.auto_run_default,
    )

    return config
