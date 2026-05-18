"""Compile-only stub for examples/quickstart.py (PS303)."""

import subprocess
import sys
from pathlib import Path

QUICKSTART = Path(__file__).parents[2] / "examples" / "quickstart.py"


def test_quickstart_example_file_exists_on_disk():
    """examples/quickstart.py should exist as a file on disk."""
    # Arrange
    path = QUICKSTART
    # Act
    exists = path.is_file()
    # Assert
    assert exists, f"missing {path}"


def test_quickstart_example_compiles_via_py_compile():
    """examples/quickstart.py should compile via py_compile with exit 0."""
    # Arrange
    cmd = [sys.executable, "-m", "py_compile", str(QUICKSTART)]
    # Act
    proc = subprocess.run(cmd, capture_output=True, text=True)
    # Assert
    assert proc.returncode == 0, f"py_compile failed: {proc.stderr}"
