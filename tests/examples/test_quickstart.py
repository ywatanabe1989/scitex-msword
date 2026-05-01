"""Compile-only stub for examples/quickstart.py (PS303)."""

import subprocess
import sys
from pathlib import Path

QUICKSTART = Path(__file__).parents[2] / "examples" / "quickstart.py"


def test_quickstart_compiles():
    assert QUICKSTART.is_file(), f"missing {QUICKSTART}"
    subprocess.run(
        [sys.executable, "-m", "py_compile", str(QUICKSTART)],
        check=True,
    )
