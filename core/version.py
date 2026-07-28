import re
from pathlib import Path


_VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def project_version() -> str:
    version = _VERSION_FILE.read_text(encoding="utf-8").strip()
    if not _SEMVER.fullmatch(version):
        raise ValueError(f"Invalid semantic version in {_VERSION_FILE}: {version!r}")
    return version
