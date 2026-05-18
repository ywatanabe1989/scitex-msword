"""Smoke tests: every example script must run to completion."""

import subprocess
import sys
from pathlib import Path

import pytest

EXAMPLES = list(Path(__file__).parents[2].joinpath("examples").glob("*.py"))


def test_examples_directory_contains_at_least_one_script():
    """The examples/ directory should contain at least one .py script."""
    # Arrange
    discovered = EXAMPLES
    # Act
    count = len(discovered)
    # Assert
    assert count > 0, "no example scripts found"


@pytest.mark.parametrize(
    "example",
    EXAMPLES,
    ids=lambda p: p.name,
)
def test_example_script_runs_to_completion_exit_zero(example, tmp_path):
    """Each example script should exit with code 0 within the timeout."""
    # Arrange
    cmd = [sys.executable, str(example)]
    # Act
    result = subprocess.run(
        cmd,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    # Assert
    assert result.returncode == 0, f"{example.name} failed: {result.stderr}"
