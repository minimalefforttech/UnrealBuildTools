from __future__ import absolute_import, unicode_literals
from typing import List
from enum import Enum, auto
from types import SimpleNamespace

class Platform(Enum):
    WIN64 = "Win64"
    LINUX = "Linux"
    MAC = "Mac"
    UNKNOWN = "Unknown"

SUPPORTED_PLATFORMS: List[Platform] = [
    Platform.WIN64,
    Platform.LINUX,
    Platform.MAC,
]

SUPPORTED_CONFIGURATIONS: List[str] = [
    "Debug",
    "Development",
    "Shipping",
    "Test"
]

LOG_LEVELS: List[str] = [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL"
]

ENV = SimpleNamespace(
    ENGINE_BASE_DIR="UBT_ENGINE_BASE_DIR"
)


# File type definitions
SOURCE_FILE_EXTENSIONS = ['.h', '.hh', '.cpp', '.cc', '.cs', '.py']
EXECUTABLE_PATTERNS = ['*.sh', '*.cmd', '*.bat', '*.exe']

# Validation settings
MAX_PATH_LENGTH = 170
THIRD_PARTY_MARKER = 'ThirdParty'

# FabURL validation
FAB_URL_PATTERN = r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}'

COMMENT_PREFIXES = ['//', '/*', '"""', "'''", '#']