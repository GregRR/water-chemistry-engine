"""Basic package tests."""

from importlib.metadata import metadata, version

import water_treatment_web


def test_package_version() -> None:
    """The import package and distribution expose the same version."""
    assert water_treatment_web.__version__ == "0.1.0"
    assert version("water-treatment-web") == water_treatment_web.__version__


def test_python_compatibility_metadata() -> None:
    """The distribution advertises the supported Python compatibility floor."""
    assert metadata("water-treatment-web")["Requires-Python"] == ">=3.11"
