"""
Pytest configuration.
Ensures the project root is importable so `from src...` works when tests
are collected from the tests/ directory.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
