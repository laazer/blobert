#!/bin/bash
cd /Users/jacobbrandt/workspace/blobert
python -m pytest tests/ci/test_formatting_check.py -v --tb=short 2>&1 | head -200
