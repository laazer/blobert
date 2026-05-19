#!/usr/bin/env python3
"""Quick test to verify formatting_check module works."""

import sys
from pathlib import Path

# Add ci/scripts to path
CI_SCRIPTS = Path(__file__).resolve().parent / "ci" / "scripts"
sys.path.insert(0, str(CI_SCRIPTS))

try:
    from gates import formatting_check
    print("✓ Module imported successfully")

    # Test basic function
    print(f"✓ run() function is callable: {callable(formatting_check.run)}")

    # Test with mocked git (no staged files)
    from unittest import mock

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
        result = formatting_check.run({})
        print(f"✓ run({{}}) returned: {type(result)}")
        print(f"  Status: {result.get('status')}")
        print(f"  Gate: {result.get('gate')}")
        print(f"  Message: {result.get('message')}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
