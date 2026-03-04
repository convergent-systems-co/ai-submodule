#!/usr/bin/env python3
"""Backward-compatible entry point. Delegates to governance.engine.policy_engine.

All logic has moved to governance/engine/policy_engine.py. This wrapper exists
so that consuming repos and CI workflows that reference governance/bin/policy-engine.py
continue to work without changes.
"""
import os
import sys

# Add the repo root to sys.path so governance.engine is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from governance.engine.policy_engine import main

if __name__ == '__main__':
    main()
