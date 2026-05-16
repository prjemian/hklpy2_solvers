"""
Shim to test if "hkl" package (libhkl) can be imported.

Importing this module succeeds only if libhkl is loadable via gi.
"""

try:
    import gi
    gi.require_version("Hkl", "5.0")
    from gi.repository import Hkl  # noqa: F401
except Exception as exc:  # ValueError from require_version, etc.
    raise ImportError(f"libhkl not available: {exc}") from exc
