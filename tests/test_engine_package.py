"""Basic package tests."""

from importlib.metadata import metadata, version

import water_chemistry_engine


def test_package_version() -> None:
    """The import package and distribution expose the release version."""
    assert water_chemistry_engine.__version__ == "0.2.0"
    assert version("water-chemistry-engine") == water_chemistry_engine.__version__


def test_python_compatibility_metadata() -> None:
    """The distribution advertises the supported Python compatibility floor."""
    assert metadata("water-chemistry-engine")["Requires-Python"] == ">=3.11"


def test_license_metadata() -> None:
    """The distribution records and packages its declared license file."""
    package_metadata = metadata("water-chemistry-engine")

    assert package_metadata["License-Expression"] == "MPL-2.0"
    assert package_metadata.get_all("License-File") == ["LICENSE"]
