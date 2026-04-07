"""
tests/conftest.py — Shared pytest configuration and fixtures
Centralizes sys.path setup so individual test files don't need it.
"""

import sys
import os

# Ensure project root is on the path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
