"""Basic package tests."""

from importlib.metadata import version

import water_treatment_engine


def test_package_version() -> None:
    """The import package and distribution expose the release version."""
    assert water_treatment_engine.__version__ == "0.2.0"
    assert version("water-treatment-engine") == water_treatment_engine.__version__
