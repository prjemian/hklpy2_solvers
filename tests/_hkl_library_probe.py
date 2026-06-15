"""
Shim to test if "hkl" package (libhkl) can be imported.

Importing this module succeeds only if libhkl is loadable via gi.

Failure is re-raised as :class:`ModuleNotFoundError` (a subclass of
:class:`ImportError`) so that :func:`pytest.importorskip` skips
correctly under both legacy pytest (``exc_type=ImportError`` default
through 9.0) and pytest >= 9.1, which defaults
``exc_type=ModuleNotFoundError`` and no longer catches a plain
:class:`ImportError` raised from a module body.  See pytest issue
`#11523 <https://github.com/pytest-dev/pytest/issues/11523>`_.
"""

try:
    import gi

    gi.require_version("Hkl", "5.0")
    from gi.repository import Hkl  # noqa: F401
except Exception as exc:  # ValueError from require_version, etc.
    raise ModuleNotFoundError(f"libhkl not available: {exc}") from exc
