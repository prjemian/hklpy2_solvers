# Copyright (c) 2026 Pete Jemian <prjemian+hklpy2@gmail.com>
# SPDX-License-Identifier: LicenseRef-UChicago-Argonne-LLC-License
"""Basic package tests."""

import re
from contextlib import nullcontext as does_not_raise

import pytest

import hklpy2_solvers


@pytest.mark.parametrize(
    "parms, context",
    [
        pytest.param(
            dict(attr="__version__"),
            does_not_raise(),
            id="has __version__",
        ),
        pytest.param(
            dict(attr="__no_such_attribute__"),
            pytest.raises(AttributeError, match=re.escape("has no attribute '__no_such_attribute__'")),
            id="missing attribute raises AttributeError",
        ),
    ],
)
def test_package_attributes(parms, context):
    with context:
        value = getattr(hklpy2_solvers, parms["attr"])
        assert isinstance(value, str)
        assert len(value) > 0
