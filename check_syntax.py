#!/usr/bin/env python3
"""Check syntax of formatting_check.py"""

import sys
import py_compile

try:
    py_compile.compile('/Users/jacobbrandt/workspace/blobert/ci/scripts/gates/formatting_check.py', doraise=True)
    print("✓ Syntax OK")
    sys.exit(0)
except py_compile.PyCompileError as e:
    print(f"✗ Syntax error: {e}")
    sys.exit(1)
