#!/bin/bash
cd /Users/jacobbrandt/workspace/blobert
python -m pytest tests/ci/test_formatting_check.py::TestRequirement03FormatterInvocation::test_black_formatter_invocation -xvs
