"""
tests/conftest.py
==================
Puts src/ (the parent of this tests/ package) on sys.path so `import config`
and `import backend` resolve regardless of the directory pytest is invoked
from — run with `pytest` from src/, or `python -m pytest src/tests` from
the repo root.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
