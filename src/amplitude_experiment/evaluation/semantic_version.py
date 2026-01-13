import re
from dataclasses import dataclass
from typing import Optional

# Major and minor should be non-negative numbers separated by a dot
MAJOR_MINOR_REGEX = r'(\d+)\.(\d+)'

# Patch should be a non-negative number
PATCH_REGEX = r'(\d+)'

# Prerelease is optional. If provided, it should be a hyphen followed by a
# series of dot separated identifiers where an identifier can contain anything in [-0-9a-zA-Z]
PRERELEASE_REGEX = r'(-(([-\w]+\.?)*))?'

# Version pattern should be major.minor(.patchAndPreRelease) where .patchAndPreRelease is optional
VERSION_PATTERN = fr'^{MAJOR_MINOR_REGEX}(\.{PATCH_REGEX}{PRERELEASE_REGEX})?$'

@dataclass
class SemanticVersion:
    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None

    @classmethod
    def parse(cls, version: Optional[str]) -> Optional['SemanticVersion']:
        """
        Parse a version string into a SemanticVersion object.
        Returns None if the version string is invalid.
        """
        if not version:
            return None

        match = re.match(VERSION_PATTERN, version)
        if not match:
            return None

        try:
            major = int(match.group(1))
            minor = int(match.group(2))
            patch = int(match.group(4)) if match.group(4) else 0
            pre_release = match.group(5) if match.group(5) else None
            return cls(major, minor, patch, pre_release)
        except (IndexError, ValueError):
            return None

    def compare_to(self, other: 'SemanticVersion') -> int:
        """
        Compare this version to another version.
        Returns:
            1 if this version is greater than the other
            -1 if this version is less than the other
            0 if the versions are equal
        """
        if self.major > other.major:
            return 1
        if self.major < other.major:
            return -1

        if self.minor > other.minor:
            return 1
        if self.minor < other.minor:
            return -1

        if self.patch > other.patch:
            return 1
        if self.patch < other.patch:
            return -1

        if self.pre_release and not other.pre_release:
            return -1
        if not self.pre_release and other.pre_release:
            return 1

        if self.pre_release and other.pre_release:
            if self.pre_release > other.pre_release:
                return 1
            if self.pre_release < other.pre_release:
                return -1
            return 0

        return 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return self.compare_to(other) == 0
