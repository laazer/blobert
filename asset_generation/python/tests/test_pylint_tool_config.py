"""Lock [tool.pylint] in pyproject.toml for pre-commit too-many-statements."""

from __future__ import annotations

import tomllib
from pathlib import Path


def test_pylint_design_max_statements_matches_hook_budget() -> None:
    root = Path(__file__).resolve().parents[1]
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    pylint_cfg = data["tool"]["pylint"]
    assert pylint_cfg["main"]["disable"] == ["all"]
    assert pylint_cfg["main"]["enable"] == ["too-many-statements"]
    assert pylint_cfg["design"]["max-statements"] == 50
