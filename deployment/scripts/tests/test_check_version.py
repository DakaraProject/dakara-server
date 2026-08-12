from io import StringIO
from pathlib import Path

import pytest
from packaging.version import Version

from scripts.check_version import check_version, extract_version


class TestExtractVersion:
    def test_extract(self, mocker):
        """Extract version from file."""
        content = """# Config file
# Version: 1.4.2"""
        mocked_read_text = mocker.patch.object(
            Path, "read_text", return_value=content, autospec=True
        )

        version = extract_version(Path("file"))

        assert version == Version("1.4.2")
        mocked_read_text.assert_called_with(Path("file"))

    def test_extract_multiple(self, mocker):
        """Extract version from file with several version strings."""
        content = """# Config file
# Version: 1.4.2
# Version: 1.4.3"""
        mocker.patch.object(Path, "read_text", return_value=content, autospec=True)

        version = extract_version(Path("file"))

        assert version == Version("1.4.2")

    def test_extract_none(self, mocker):
        """Try to extract version from file with no version string."""
        content = """# Config file"""
        mocker.patch.object(Path, "read_text", return_value=content, autospec=True)

        with pytest.raises(ValueError):
            extract_version(Path("file"))


class TestCheckVersion:
    def test_check_same(self, mocker):
        """Check when reference and candidate have the same version."""
        mocked_extract_version = mocker.patch(
            "scripts.check_version.extract_version", autoset=True
        )
        mocked_extract_version.return_value = Version("1.4.2")

        output = StringIO()
        check_version(Path("reference"), Path("candidate"), output=output)
        content = output.getvalue()

        assert not content

    def test_check_reference_older(self, mocker):
        """Check when reference is older than candidate."""
        mocked_extract_version = mocker.patch(
            "scripts.check_version.extract_version", autoset=True
        )
        mocked_extract_version.side_effect = [Version("1.4.2"), Version("1.4.3")]

        output = StringIO()
        check_version(Path("reference"), Path("candidate"), output=output)
        content = output.getvalue()

        assert not content

    def test_check_reference_newer(self, mocker):
        """Check when reference is newer than candidate."""
        mocked_extract_version = mocker.patch(
            "scripts.check_version.extract_version", autoset=True
        )
        mocked_extract_version.side_effect = [Version("1.4.3"), Version("1.4.2")]

        output = StringIO()
        check_version(Path("reference"), Path("candidate"), output=output)
        content = output.getvalue()

        assert content
        assert "Configuration file candidate is outdated" in content
        assert "You should update it from reference" in content
