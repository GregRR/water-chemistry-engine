"""Basic package tests."""

import water_treatment_web


def test_package_version() -> None:
    """The package exposes its current version."""
    assert water_treatment_web.__version__ == "0.1.0"
