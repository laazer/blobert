#!/usr/bin/env python3
"""Simple test runner to check formatting_check tests."""

import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest",
     "tests/ci/test_formatting_check.py::TestRequirement03FormatterInvocation::test_black_formatter_invocation",
     "-xvs"],
    cwd="/Users/jacobbrandt/workspace/blobert"
)

sys.exit(result.returncode)
