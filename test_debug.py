#!/usr/bin/env python3
"""Quick debug script to test formatting_check."""

import sys
from pathlib import Path
from unittest import mock

# Add ci/scripts to path
ci_scripts = Path(__file__).parent / "ci" / "scripts"
sys.path.insert(0, str(ci_scripts))

from gates import formatting_check

# Test TV-07: Partial formatting needed
print("Testing TV-07: Partial formatting needed")

with mock.patch("subprocess.run") as mock_run:
    def run_side_effect(cmd, *args, **kwargs):
        print(f"  subprocess.run called with: {cmd}")
        if "git" in str(cmd) and "diff" in str(cmd) and "--cached" in str(cmd):
            print(f"    → returning staged files: a.py, b.py, c.py")
            return mock.Mock(returncode=0, stdout="a.py\nb.py\nc.py", stderr="")
        elif "black" in str(cmd):
            print(f"    → black formatter ran")
            return mock.Mock(returncode=0, stdout="", stderr="")
        elif "git" in str(cmd) and "diff" in str(cmd) and "--cached" not in str(cmd):
            print(f"    → returning changed files: a.py, c.py")
            # Only a.py and c.py changed
            return mock.Mock(returncode=0, stdout="--- a/a.py\n+++ b/a.py\n--- a/c.py", stderr="")
        elif "git" in str(cmd) and "add" in str(cmd):
            print(f"    → git add called")
            return mock.Mock(returncode=0, stdout="", stderr="")
        else:
            print(f"    → unknown command, returning empty")
            return mock.Mock(returncode=0, stdout="", stderr="")

    mock_run.side_effect = run_side_effect
    result = formatting_check.run({})

print(f"\nResult:")
print(f"  status: {result.get('status')}")
print(f"  formatting_changed: {result.get('formatting_changed')}")
print(f"  artifacts: {result.get('artifacts')}")
print(f"  message: {result.get('message')}")

# Check assertions
assert result["status"] == "PASS", f"Expected PASS but got {result['status']}"
assert result["formatting_changed"] is True, f"Expected formatting_changed=True but got {result.get('formatting_changed')}"
print("\n✓ TV-07 test passed!")
