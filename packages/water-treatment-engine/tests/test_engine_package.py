"""Basic package tests."""

import water_treatment_engine


def test_package_version() -> None:
    """The package exposes its current version."""
    assert water_treatment_engine.__version__ == "0.1.0"
