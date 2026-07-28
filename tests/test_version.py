import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.version import project_version


class VersionTests(unittest.TestCase):
    def test_project_version_comes_from_version_file(self) -> None:
        expected = (
            Path(__file__).resolve().parent.parent / "VERSION"
        ).read_text(encoding="utf-8").strip()
        self.assertEqual(project_version(), expected)


if __name__ == "__main__":
    unittest.main()
