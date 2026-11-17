"""Bounded contexts of the modular monolith.

Each context follows the same layout (domain / application / infrastructure / presentation)
and exposes a single public facade, ``api.py``, which is the only module other contexts may import.
"""
